from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from uuid import uuid4
import hashlib
import json
import re
import shutil
import stat
import zipfile

from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_downloader import ModrinthDownloader
from src.core.modrinth.modrinth_pack_registry import ModrinthPackRegistry
from src.models.modrinth.install_result import ModrinthModpackInstallResult


class ModrinthPackInstaller:
    INDEX_NAME = "modrinth.index.json"
    FORMAT_VERSION = 1
    MAX_WORKERS = 8
    MAX_INDEX_BYTES = 8 * 1024 * 1024
    MAX_FILES = 20_000
    MAX_TOTAL_DOWNLOAD_BYTES = 50 * 1024 * 1024 * 1024
    MAX_OVERRIDE_BYTES = 2 * 1024 * 1024 * 1024
    MAX_PATH_LENGTH = 240
    RESERVED_ROOT_NAMES = {"instance.json", "settings.json", ".mcw"}
    INSTANCE_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1F]{1,80}$')

    @staticmethod
    def install(project_id: str, version_id: str, instance_name: str, install_optional_files: bool = True, allowed_version_types: tuple[str, ...] | list[str] | set[str] | None = None) -> ModrinthModpackInstallResult:
        project = ModrinthClient.get_project(project_id)
        requested_name = str(instance_name or "").strip()
        base_name = ModrinthPackInstaller._validated_instance_name(requested_name or project.title)
        normalized_name = base_name if requested_name else InstanceManager.next_available_name(base_name)
        if requested_name and InstanceManager.is_instance_exist(normalized_name):
            raise RuntimeError(f"Instance '{normalized_name}' already exists.")

        if project.project_type != "modpack":
            raise RuntimeError(f"'{project.title}' is not a Modrinth modpack.")
        version = ModrinthClient.get_version(version_id)
        if version.project_id != project.project_id:
            raise RuntimeError("The selected Modrinth version does not belong to this modpack.")
        allowed_types = ModrinthClient.normalize_version_types(allowed_version_types)
        if version.version_type not in allowed_types:
            raise RuntimeError(f"Modrinth modpack version '{version.version_number}' uses the disabled {version.version_type} channel.")
        pack_file = version.primary_file(".mrpack")
        pack_path = Paths.modrinth_pack_cache(project.project_id, version.version_id, pack_file.filename)
        ModrinthDownloader.download_file(pack_file, pack_path)

        staging = Paths.modrinth_staging_root() / uuid4().hex
        staging.mkdir(parents=True, exist_ok=False)
        created_instance = None
        try:
            with zipfile.ZipFile(pack_path, "r") as archive:
                index = ModrinthPackInstaller._read_index(archive)
                minecraft_version, loader_version = ModrinthPackInstaller._parse_dependencies(index)
                selected_files, skipped_optional, skipped_server = ModrinthPackInstaller._selected_files(index, install_optional_files)
                managed_files = {entry["path"].casefold(): entry for entry in ModrinthPackInstaller._managed_download_entries(selected_files)}
                ModrinthPackInstaller._download_files(selected_files, staging)
                for entry in ModrinthPackInstaller._extract_layer(archive, "overrides", staging):
                    managed_files[entry["path"].casefold()] = entry
                for entry in ModrinthPackInstaller._extract_layer(archive, "client-overrides", staging):
                    managed_files[entry["path"].casefold()] = entry

            base_version = VersionManager.load(minecraft_version)
            resolved_loader = ModLoaderManager.resolve(minecraft_version, ModLoaderManager.FABRIC, loader_version)
            ModLoaderManager.prepare(base_version, *resolved_loader)
            created_instance = InstanceManager.create(name=normalized_name, version=base_version, mod_loader=resolved_loader)
            shutil.copytree(staging, created_instance.instance_dir, dirs_exist_ok=True)
            ModrinthPackInstaller._write_metadata(created_instance.instance_dir, project.project_id, version.version_id, project.title, version.version_number, minecraft_version, loader_version, list(managed_files.values()), install_optional_files)
            return ModrinthModpackInstallResult(instance=created_instance, pack_name=project.title, pack_version=version.version_number, installed_files=len(selected_files), skipped_optional_files=skipped_optional, skipped_server_files=skipped_server)
        except Exception:
            if created_instance is not None:
                InstanceManager.delete_instance(created_instance.name)
            raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    @staticmethod
    def inspect(pack_path: Path) -> dict:
        with zipfile.ZipFile(pack_path, "r") as archive:
            index = ModrinthPackInstaller._read_index(archive)
            minecraft_version, loader_version = ModrinthPackInstaller._parse_dependencies(index)
        return {"name": str(index.get("name") or ""), "summary": str(index.get("summary") or ""), "minecraft": minecraft_version, "fabric_loader": loader_version, "files": len(index.get("files", []))}

    @staticmethod
    def _read_index(archive: zipfile.ZipFile) -> dict:
        try:
            raw = archive.read(ModrinthPackInstaller.INDEX_NAME)
        except KeyError as error:
            raise RuntimeError("The .mrpack file is missing modrinth.index.json.") from error
        if len(raw) > ModrinthPackInstaller.MAX_INDEX_BYTES:
            raise RuntimeError("modrinth.index.json is too large to process safely.")
        try:
            index = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Invalid modrinth.index.json: {error}") from error
        if not isinstance(index, dict):
            raise RuntimeError("modrinth.index.json must contain an object.")
        if int(index.get("formatVersion", 0) or 0) != ModrinthPackInstaller.FORMAT_VERSION:
            raise RuntimeError(f"Unsupported Modrinth pack format version: {index.get('formatVersion')}")
        if str(index.get("game") or "").strip().lower() != "minecraft":
            raise RuntimeError("This Modrinth pack is not for Minecraft.")
        if not isinstance(index.get("files"), list) or not isinstance(index.get("dependencies"), dict):
            raise RuntimeError("The Modrinth pack index is incomplete.")
        return index

    @staticmethod
    def _parse_dependencies(index: dict) -> tuple[str, str]:
        dependencies = index.get("dependencies", {})
        minecraft_version = str(dependencies.get("minecraft") or "").strip()
        fabric_loader = str(dependencies.get("fabric-loader") or "").strip()
        unsupported_loaders = [key for key in ("forge", "neoforge", "quilt-loader") if dependencies.get(key)]
        if unsupported_loaders:
            raise RuntimeError(f"This modpack uses an unsupported loader: {', '.join(unsupported_loaders)}")
        if not minecraft_version:
            raise RuntimeError("The modpack does not declare a Minecraft version.")
        if not fabric_loader:
            raise RuntimeError("Only Fabric Modrinth modpacks are supported in this release.")
        return minecraft_version, fabric_loader

    @staticmethod
    def _selected_files(index: dict, install_optional_files: bool) -> tuple[list[dict], int, int]:
        selected: list[dict] = []
        skipped_optional = 0
        skipped_server = 0
        files = index.get("files", [])
        if len(files) > ModrinthPackInstaller.MAX_FILES:
            raise RuntimeError("The modpack contains too many files to install safely.")
        total_size = 0
        for item in files:
            if not isinstance(item, dict):
                raise RuntimeError("The modpack contains an invalid file entry.")
            client_state = str((item.get("env") or {}).get("client") or "required").strip().lower() if isinstance(item.get("env"), dict) else "required"
            if client_state == "unsupported":
                skipped_server += 1
                continue
            if client_state == "optional" and not install_optional_files:
                skipped_optional += 1
                continue
            ModrinthPackInstaller._safe_relative_path(str(item.get("path") or ""))
            hashes = item.get("hashes", {}) if isinstance(item.get("hashes"), dict) else {}
            if not str(hashes.get("sha1") or "") or not str(hashes.get("sha512") or ""):
                raise RuntimeError(f"Modpack file '{item.get('path')}' is missing required hashes.")
            downloads = item.get("downloads", [])
            if not isinstance(downloads, list) or not downloads:
                raise RuntimeError(f"Modpack file '{item.get('path')}' has no download URL.")
            file_size = int(item.get("fileSize", 0) or 0)
            if file_size < 0:
                raise RuntimeError(f"Modpack file '{item.get('path')}' has an invalid size.")
            total_size += file_size
            if total_size > ModrinthPackInstaller.MAX_TOTAL_DOWNLOAD_BYTES:
                raise RuntimeError("The modpack download is larger than the configured safety limit.")
            selected.append(item)
        return selected, skipped_optional, skipped_server

    @staticmethod
    def _download_files(files: list[dict], staging: Path) -> None:
        def download(item: dict) -> Path:
            relative = ModrinthPackInstaller._safe_relative_path(str(item.get("path") or ""))
            hashes = item.get("hashes", {})
            return ModrinthDownloader.download_urls(urls=tuple(str(url) for url in item.get("downloads", [])), destination=staging.joinpath(*relative.parts), sha1=str(hashes.get("sha1") or ""), sha512=str(hashes.get("sha512") or ""), expected_size=int(item.get("fileSize", 0) or 0), restrict_hosts=True)

        with ThreadPoolExecutor(max_workers=min(ModrinthPackInstaller.MAX_WORKERS, max(1, len(files)))) as executor:
            futures = [executor.submit(download, item) for item in files]
            for future in as_completed(futures):
                future.result()

    @staticmethod
    def _managed_download_entries(files: list[dict]) -> list[dict]:
        managed: list[dict] = []
        for item in files:
            relative = ModrinthPackInstaller._safe_relative_path(str(item.get("path") or ""))
            hashes = item.get("hashes", {}) if isinstance(item.get("hashes"), dict) else {}
            managed.append({"path": relative.as_posix(), "sha1": str(hashes.get("sha1") or "").lower(), "sha512": str(hashes.get("sha512") or "").lower(), "size": int(item.get("fileSize", 0) or 0), "source": "download"})
        return managed

    @staticmethod
    def _extract_layer(archive: zipfile.ZipFile, prefix: str, staging: Path) -> list[dict]:
        normalized_prefix = prefix.rstrip("/") + "/"
        extracted_size = 0
        managed: list[dict] = []
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            if not name.startswith(normalized_prefix) or name.endswith("/"):
                continue
            if stat.S_ISLNK((info.external_attr >> 16) & 0xFFFF):
                raise RuntimeError(f"Symbolic links are not allowed in modpack overrides: {name}")
            extracted_size += int(info.file_size or 0)
            if extracted_size > ModrinthPackInstaller.MAX_OVERRIDE_BYTES:
                raise RuntimeError(f"The {prefix} layer is larger than the configured safety limit.")
            relative = ModrinthPackInstaller._safe_relative_path(name[len(normalized_prefix):])
            target = staging.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            sha1 = hashlib.sha1()
            sha512 = hashlib.sha512()
            written = 0
            with archive.open(info, "r") as source, target.open("wb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    sha1.update(chunk)
                    sha512.update(chunk)
                    written += len(chunk)
            managed.append({"path": relative.as_posix(), "sha1": sha1.hexdigest(), "sha512": sha512.hexdigest(), "size": written, "source": prefix})
        return managed

    @staticmethod
    def _safe_relative_path(value: str) -> PurePosixPath:
        normalized = str(value).replace("\\", "/").strip()
        path = PurePosixPath(normalized)
        if len(normalized) > ModrinthPackInstaller.MAX_PATH_LENGTH:
            raise RuntimeError(f"Path is too long for a Windows instance: {value!r}")
        if not normalized or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise RuntimeError(f"Unsafe path in Modrinth pack: {value!r}")
        first = path.parts[0].casefold()
        if first in ModrinthPackInstaller.RESERVED_ROOT_NAMES or ":" in first:
            raise RuntimeError(f"Reserved path in Modrinth pack: {value!r}")
        return path

    @staticmethod
    def _validated_instance_name(value: str) -> str:
        name = str(value).strip()
        if not name or name in {".", ".."} or name.endswith((".", " ")) or not ModrinthPackInstaller.INSTANCE_NAME_PATTERN.fullmatch(name):
            raise RuntimeError("The modpack instance name contains invalid Windows filename characters or is longer than 80 characters.")
        return name

    @staticmethod
    def _write_metadata(instance_dir: Path, project_id: str, version_id: str, title: str, version_number: str, minecraft_version: str, loader_version: str, managed_files: list[dict], install_optional_files: bool) -> None:
        ModrinthPackRegistry.save(instance_dir, {"projectId": project_id, "versionId": version_id, "name": title, "versionNumber": version_number, "minecraftVersion": minecraft_version, "loader": "fabric", "loaderVersion": loader_version, "installOptionalFiles": bool(install_optional_files), "managedFiles": managed_files})
