from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json
import shutil
import zipfile

from src.core.fs.paths import Paths
from src.core.instance.errors import InstanceModChangeBlockedError
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.models.instance.instance import Instance
from src.models.mod.mod_info import ModInfo


class ModManager:
    DISABLED_SUFFIX = ".disabled"

    @staticmethod
    def mods_dir(instance: Instance) -> Path:
        return Paths.instance_mods_dir(instance)

    @staticmethod
    def list_mods(instance: Instance) -> list[ModInfo]:
        directory = ModManager.mods_dir(instance)
        paths = [path for path in directory.iterdir() if path.is_file() and ModManager._is_mod_file(path)]
        return sorted((ModManager.read_mod(path) for path in paths), key=lambda mod: (not mod.enabled, mod.name.casefold(), mod.file_name.casefold()))

    @staticmethod
    def add_mods(instance: Instance, source_paths: Iterable[Path], replace: bool = False) -> list[ModInfo]:
        ModManager._ensure_modifiable(instance)
        destination_dir = ModManager.mods_dir(instance)
        added: list[ModInfo] = []

        for source in source_paths:
            source = Path(source)
            if not source.is_file() or source.suffix.lower() != ".jar":
                raise RuntimeError(f"Mod file must be a .jar file: {source.name}")

            metadata = ModManager.read_mod(source)
            if metadata.status in {"Broken JAR", "Not Fabric"}:
                raise RuntimeError(metadata.error or f"'{source.name}' is not a Fabric mod.")

            destination = destination_dir / source.name
            disabled_destination = destination.with_name(destination.name + ModManager.DISABLED_SUFFIX)
            source_resolved = source.resolve()
            destination_resolved = destination.resolve()

            if source_resolved == destination_resolved:
                if not replace:
                    raise FileExistsError(f"Mod already exists: {source.name}")
                added.append(ModManager.read_mod(destination))
                continue

            conflicts = [path for path in (destination, disabled_destination) if path.exists()]

            if conflicts and not replace:
                raise FileExistsError(f"Mod already exists: {source.name}")

            temporary_path = destination.with_name(destination.name + ".part")
            try:
                shutil.copy2(source, temporary_path)
                copied = ModManager.read_mod(temporary_path)
                if copied.status in {"Broken JAR", "Not Fabric"}:
                    raise RuntimeError(copied.error or f"'{source.name}' is not a Fabric mod.")
                disabled_destination.unlink(missing_ok=True)
                temporary_path.replace(destination)
            finally:
                temporary_path.unlink(missing_ok=True)

            added.append(ModManager.read_mod(destination))

        return added

    @staticmethod
    def remove_mods(instance: Instance, paths: Iterable[Path]) -> None:
        ModManager._ensure_modifiable(instance)
        directory = ModManager.mods_dir(instance).resolve()

        for path in paths:
            candidate = Path(path).resolve()
            if candidate.parent != directory:
                raise RuntimeError("Refusing to remove a file outside the instance mods folder.")
            candidate.unlink(missing_ok=True)

    @staticmethod
    def set_enabled(instance: Instance, paths: Iterable[Path], enabled: bool) -> list[ModInfo]:
        ModManager._ensure_modifiable(instance)
        directory = ModManager.mods_dir(instance).resolve()
        changed: list[ModInfo] = []

        for path in paths:
            source = Path(path).resolve()
            if source.parent != directory or not source.exists():
                raise RuntimeError("Mod file no longer exists in this instance.")

            currently_enabled = not source.name.endswith(ModManager.DISABLED_SUFFIX)
            if currently_enabled == enabled:
                changed.append(ModManager.read_mod(source))
                continue

            if enabled:
                target = source.with_name(source.name[:-len(ModManager.DISABLED_SUFFIX)])
            else:
                target = source.with_name(source.name + ModManager.DISABLED_SUFFIX)

            if target.exists():
                raise FileExistsError(f"Cannot change mod state because '{target.name}' already exists.")

            source.replace(target)
            changed.append(ModManager.read_mod(target))

        return changed

    @staticmethod
    def read_mod(path: Path) -> ModInfo:
        path = Path(path)
        enabled = not path.name.endswith(ModManager.DISABLED_SUFFIX)
        file_name = path.name[:-len(ModManager.DISABLED_SUFFIX)] if not enabled else path.name

        try:
            with zipfile.ZipFile(path, "r") as archive:
                try:
                    raw_metadata = archive.read("fabric.mod.json")
                except KeyError:
                    return ModManager._invalid_mod(path, file_name, enabled, "Not Fabric", "fabric.mod.json is missing.")
        except (OSError, zipfile.BadZipFile) as error:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", str(error))

        try:
            data = json.loads(raw_metadata.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", f"Invalid fabric.mod.json: {error}")

        if not isinstance(data, dict):
            return ModManager._invalid_mod(path, file_name, enabled, "Broken JAR", "fabric.mod.json must contain an object.")

        mod_id = str(data.get("id") or "").strip()
        version = str(data.get("version") or "Unknown").strip()
        name = str(data.get("name") or mod_id or Path(file_name).stem).strip()
        environment = str(data.get("environment") or "*").strip()
        status = "Server only" if environment == "server" else "Ready"
        error = "This mod declares a server-only environment." if environment == "server" else ""

        if not mod_id:
            status = "Broken metadata"
            error = "Fabric mod id is missing."

        return ModInfo(
            path=path,
            file_name=file_name,
            enabled=enabled,
            mod_id=mod_id or "unknown",
            name=name,
            version=version,
            description=str(data.get("description") or "").strip(),
            environment=environment,
            authors=ModManager._parse_authors(data.get("authors")),
            licenses=ModManager._parse_licenses(data.get("license")),
            dependencies=dict(data.get("depends") or {}) if isinstance(data.get("depends"), dict) else {},
            status=status,
            error=error,
        )

    @staticmethod
    def _ensure_modifiable(instance: Instance) -> None:
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name != ModLoaderManager.FABRIC:
            raise RuntimeError("This instance does not use Fabric Loader.")
        if InstanceRunLock.is_active(instance):
            raise InstanceModChangeBlockedError(instance.name)

    @staticmethod
    def _is_mod_file(path: Path) -> bool:
        lower_name = path.name.lower()
        return lower_name.endswith(".jar") or lower_name.endswith(".jar" + ModManager.DISABLED_SUFFIX)

    @staticmethod
    def _parse_authors(value: object) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        authors: list[str] = []
        for author in value:
            if isinstance(author, str) and author.strip():
                authors.append(author.strip())
            elif isinstance(author, dict):
                name = str(author.get("name") or "").strip()
                if name:
                    authors.append(name)
        return tuple(authors)

    @staticmethod
    def _parse_licenses(value: object) -> tuple[str, ...]:
        if isinstance(value, str) and value.strip():
            return (value.strip(),)
        if isinstance(value, list):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return ()

    @staticmethod
    def _invalid_mod(path: Path, file_name: str, enabled: bool, status: str, error: str) -> ModInfo:
        return ModInfo(path=path, file_name=file_name, enabled=enabled, mod_id="unknown", name=Path(file_name).stem, version="Unknown", status=status, error=error)
