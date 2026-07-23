from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import shutil

from src.core.curseforge.curseforge_registry import CurseForgeRegistry
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.mod.mod_manager import ModManager
from src.models.curseforge.manual_download import CurseForgeManualDownload
from src.models.instance.instance import Instance


class CurseForgeManualInstaller:
    @staticmethod
    def install(instance: Instance, requirement: CurseForgeManualDownload, source: Path) -> str:
        path = Path(source)
        if InstanceRunLock.is_active(instance):
            raise RuntimeError("Close Minecraft before importing a manually downloaded mod.")
        if not path.is_file():
            raise RuntimeError("The selected CurseForge file does not exist.")
        if requirement.file_size > 0 and path.stat().st_size != requirement.file_size:
            raise RuntimeError(
                f"The selected file has the wrong size. Expected {requirement.file_size} bytes, got {path.stat().st_size} bytes."
            )
        if requirement.sha1:
            digest = CurseForgeManualInstaller._sha1(path)
            if digest.casefold() != requirement.sha1.casefold():
                raise RuntimeError("The selected file does not match the expected CurseForge SHA-1 checksum.")
        added = ModManager.add_mods(instance, [path], replace=True)
        if not added:
            raise RuntimeError("The selected file could not be added to the instance.")
        installed_name = added[0].file_name
        registry = CurseForgeRegistry.load(instance)
        mods = registry.setdefault("mods", {})
        previous = mods.get(str(requirement.project_id), {}) if isinstance(mods.get(str(requirement.project_id)), dict) else {}
        old_name = str(previous.get("fileName") or "")
        if old_name and old_name.casefold() != installed_name.casefold():
            old_path = CurseForgeRegistry.safe_tracked_path(instance, old_name)
            if old_path is not None:
                old_path.unlink(missing_ok=True)
                old_path.with_name(old_path.name + ModManager.DISABLED_SUFFIX).unlink(missing_ok=True)
        mods[str(requirement.project_id)] = {
            **previous,
            "projectId": requirement.project_id,
            "fileId": requirement.file_id,
            "fileName": installed_name,
            "displayName": requirement.project_name,
            "sha1": requirement.sha1,
            "size": requirement.file_size,
            "downloadUrl": "",
            "source": "curseforge",
            "pendingDownload": False,
            "lastDownloadError": "",
            "manualImport": True,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        CurseForgeRegistry.save(instance, registry)
        return installed_name

    @staticmethod
    def copy_to_cache(source: Path, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".part")
        shutil.copy2(source, temporary)
        temporary.replace(destination)
        return destination

    @staticmethod
    def _sha1(path: Path) -> str:
        digest = hashlib.sha1(usedforsecurity=False)
        with path.open("rb") as input_file:
            while chunk := input_file.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()
