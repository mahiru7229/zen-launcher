from __future__ import annotations

from pathlib import Path, PurePosixPath
import json
import re
import shutil
import stat
import zipfile

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_downloader import CurseForgeDownloader
from src.core.curseforge.curseforge_pack_registry import CurseForgePackRegistry
from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.install_result import CurseForgeModpackInstallResult
from src.models.progress.progress_stage import ProgressStage


class CurseForgePackInstaller:
    MANIFEST_NAME = "manifest.json"
    MAX_MANIFEST_BYTES = 4 * 1024 * 1024
    MAX_FILES = 5000
    MAX_OVERRIDE_BYTES = 2 * 1024 * 1024 * 1024
    MAX_PATH_LENGTH = 240
    MAX_WORKERS = 8
    INSTANCE_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1F]{1,80}$')

    @staticmethod
    def install(project_id: int, file_id: int, instance_name: str, install_optional_files: bool = True, allowed_release_types: tuple[str, ...] | list[str] | set[str] | None = None, reporter: ProgressReporter | None = None) -> CurseForgeModpackInstallResult:
        name = CurseForgePackInstaller._validated_instance_name(instance_name)
        if InstanceManager.is_instance_exist(name):
            raise RuntimeError(f"Instance '{name}' already exists.")
        allowed = CurseForgeClient.normalize_release_types(allowed_release_types)
        project = CurseForgeClient.get_project(project_id)
        file = CurseForgeClient.get_file(project_id, file_id)
        if file.release_type not in allowed:
            raise RuntimeError(f"CurseForge modpack file '{file.display_name}' uses the disabled {file.release_type} channel.")
        pack_path = Paths.curseforge_pack_cache(project_id, file_id, file.file_name)
        CurseForgeDownloader.download_file(file, pack_path, reporter=reporter, stage=ProgressStage.DOWNLOADING_MODPACK, message=f"Downloading {project.name} manifest...", project_name=project.name)

        with zipfile.ZipFile(pack_path, "r") as archive:
            manifest = CurseForgePackInstaller._read_manifest(archive)
            minecraft_version, forge_version = CurseForgePackInstaller._parse_loader(manifest)
            entries, skipped = CurseForgePackInstaller._resolve_files(manifest, minecraft_version, install_optional_files, reporter)
            version = VersionManager.load(minecraft_version)
            resolved_loader = ModLoaderManager.resolve(minecraft_version, ModLoaderManager.FORGE, forge_version)
            ModLoaderManager.prepare(version, *resolved_loader, reporter=reporter)
            instance = InstanceManager.create(name=name, version=version, mod_loader=resolved_loader)
            try:
                CurseForgePackInstaller._extract_overrides(archive, str(manifest.get("overrides") or "overrides"), Path(instance.instance_dir), reporter)
                CurseForgePackRegistry.save(instance, {
                    "projectId": int(project_id),
                    "fileId": int(file_id),
                    "name": project.name,
                    "versionName": file.display_name,
                    "minecraftVersion": minecraft_version,
                    "loader": "forge",
                    "loaderVersion": forge_version,
                    "installOptionalFiles": bool(install_optional_files),
                    "managedFiles": entries,
                    "lastDownloadFailures": [],
                })
            except Exception:
                InstanceManager.delete_instance(name)
                raise
        return CurseForgeModpackInstallResult(instance=instance, pack_name=project.name, pack_version=file.display_name, managed_files=len(entries), skipped_optional_files=skipped)

    @staticmethod
    def _read_manifest(archive: zipfile.ZipFile) -> dict:
        try:
            info = archive.getinfo(CurseForgePackInstaller.MANIFEST_NAME)
        except KeyError as error:
            raise RuntimeError("The CurseForge modpack is missing manifest.json.") from error
        if info.file_size > CurseForgePackInstaller.MAX_MANIFEST_BYTES:
            raise RuntimeError("CurseForge manifest.json is too large to process safely.")
        try:
            data = json.loads(archive.read(info).decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Invalid CurseForge manifest.json: {error}") from error
        if not isinstance(data, dict) or not isinstance(data.get("minecraft"), dict) or not isinstance(data.get("files"), list):
            raise RuntimeError("CurseForge manifest.json is incomplete.")
        if len(data["files"]) > CurseForgePackInstaller.MAX_FILES:
            raise RuntimeError("The CurseForge modpack contains too many files to install safely.")
        return data

    @staticmethod
    def _parse_loader(manifest: dict) -> tuple[str, str]:
        minecraft = manifest.get("minecraft", {})
        game_version = str(minecraft.get("version") or "").strip()
        loaders = minecraft.get("modLoaders") if isinstance(minecraft.get("modLoaders"), list) else []
        selected = next((item for item in loaders if isinstance(item, dict) and str(item.get("id") or "").lower().startswith("forge-") and bool(item.get("primary", False))), None)
        if selected is None:
            selected = next((item for item in loaders if isinstance(item, dict) and str(item.get("id") or "").lower().startswith("forge-")), None)
        if not game_version:
            raise RuntimeError("The CurseForge modpack does not declare a Minecraft version.")
        if selected is None:
            raise RuntimeError("Only Forge CurseForge modpacks are supported in v0.7.0 Beta 1.")
        loader_id = str(selected.get("id") or "")
        forge_version = loader_id.split("-", 1)[1].strip() if "-" in loader_id else ""
        if not forge_version:
            raise RuntimeError("The CurseForge modpack declares an invalid Forge version.")
        return game_version, forge_version

    @staticmethod
    def _resolve_files(manifest: dict, game_version: str, install_optional_files: bool, reporter: ProgressReporter | None) -> tuple[list[dict], int]:
        raw_files = manifest.get("files", [])
        selected = [item for item in raw_files if isinstance(item, dict) and (bool(item.get("required", True)) or install_optional_files)]
        skipped = len(raw_files) - len(selected)
        normalized: list[tuple[int, int, bool]] = []
        for item in selected:
            project_id = int(item.get("projectID") or item.get("projectId") or 0)
            file_id = int(item.get("fileID") or item.get("fileId") or 0)
            if project_id <= 0 or file_id <= 0:
                raise RuntimeError("The CurseForge modpack contains an invalid project or file ID.")
            normalized.append((project_id, file_id, bool(item.get("required", True))))
        if reporter is not None:
            reporter.files(stage=ProgressStage.CHECKING_MODPACK, message="Reading CurseForge modpack file metadata...", current=0, total=len(normalized))

        files = CurseForgeClient.get_files_batch([file_id for _project_id, file_id, _required in normalized])
        results: list[dict] = []
        for completed, (project_id, file_id, required) in enumerate(normalized, start=1):
            file = files.get(file_id)
            if file is None or file.project_id != project_id:
                file = CurseForgeClient.get_file(project_id, file_id)
            if game_version and game_version not in file.game_versions:
                raise RuntimeError(f"CurseForge file '{file.file_name}' does not support Minecraft {game_version}.")
            results.append({
                "projectId": project_id,
                "fileId": file_id,
                "fileName": file.file_name,
                "path": f"mods/{file.file_name}",
                "displayName": file.display_name,
                "sha1": file.sha1,
                "size": file.file_length,
                "downloadUrl": file.download_url,
                "required": required,
            })
            if reporter is not None:
                reporter.files(stage=ProgressStage.CHECKING_MODPACK, message="Reading CurseForge modpack file metadata...", current=completed, total=len(normalized))
        return sorted(results, key=lambda item: (item["projectId"], item["fileId"])), skipped

    @staticmethod
    def _extract_overrides(archive: zipfile.ZipFile, prefix: str, destination: Path, reporter: ProgressReporter | None) -> None:
        normalized_prefix = str(prefix).replace("\\", "/").strip("/") + "/"
        entries = [info for info in archive.infolist() if info.filename.replace("\\", "/").startswith(normalized_prefix) and not info.is_dir()]
        total_bytes = sum(max(0, int(info.file_size or 0)) for info in entries)
        if total_bytes > CurseForgePackInstaller.MAX_OVERRIDE_BYTES:
            raise RuntimeError("The CurseForge override layer is larger than the configured safety limit.")
        written = 0
        if reporter is not None:
            reporter.bytes(stage=ProgressStage.INSTALLING_MOD_LOADER, message="Extracting CurseForge overrides...", current=0, total=total_bytes)
        for info in entries:
            if stat.S_ISLNK((info.external_attr >> 16) & 0xFFFF):
                raise RuntimeError(f"Symbolic links are not allowed in CurseForge overrides: {info.filename}")
            name = info.filename.replace("\\", "/")[len(normalized_prefix):]
            relative = CurseForgePackInstaller._safe_relative_path(name)
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
                    written += len(chunk)
                    if reporter is not None:
                        reporter.bytes(stage=ProgressStage.INSTALLING_MOD_LOADER, message=f"Extracting {relative.as_posix()}...", current=written, total=total_bytes)

    @staticmethod
    def _safe_relative_path(value: str) -> PurePosixPath:
        normalized = str(value).replace("\\", "/").strip()
        path = PurePosixPath(normalized)
        if len(normalized) > CurseForgePackInstaller.MAX_PATH_LENGTH or not normalized or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise RuntimeError(f"Unsafe path in CurseForge modpack: {value!r}")
        if ":" in path.parts[0]:
            raise RuntimeError(f"Unsafe Windows path in CurseForge modpack: {value!r}")
        return path

    @staticmethod
    def _validated_instance_name(value: str) -> str:
        name = str(value).strip()
        if not name or name in {".", ".."} or name.endswith((".", " ")) or not CurseForgePackInstaller.INSTANCE_NAME_PATTERN.fullmatch(name):
            raise RuntimeError("The modpack instance name contains invalid Windows filename characters or is longer than 80 characters.")
        return name
