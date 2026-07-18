from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_downloader import CurseForgeDownloader
from src.core.curseforge.curseforge_pack_registry import CurseForgePackRegistry
from src.core.curseforge.curseforge_registry import CurseForgeRegistry
from src.core.fs.paths import Paths
from src.core.mod.mod_manager import ModManager
from src.core.network.download_pause import is_download_paused
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.file import CurseForgeFile
from src.models.instance.instance import Instance
from src.models.progress.progress_stage import ProgressStage


class CurseForgeContentManager:
    MAX_DOWNLOAD_ROUNDS = 3
    MAX_WORKERS = 8

    @staticmethod
    def ensure(instance: Instance, reporter: ProgressReporter | None = None, block_launch_on_failure: bool = True) -> tuple[str, ...]:
        if getattr(instance, "instance_dir", None) is None:
            return ()
        pack = CurseForgePackRegistry.load(instance)
        registry = CurseForgeRegistry.load(instance)
        pack_entries = [entry for entry in pack.get("managedFiles", []) if isinstance(entry, dict)]
        mod_entries = [entry for entry in registry.get("mods", {}).values() if isinstance(entry, dict)]
        if not pack_entries and not mod_entries:
            return ()
        warnings: list[str] = []
        last_errors: dict[str, str] = {}

        for round_number in range(1, CurseForgeContentManager.MAX_DOWNLOAD_ROUNDS + 1):
            missing = CurseForgeContentManager._check_all(instance, pack_entries, mod_entries, reporter, round_number)
            if not missing:
                if pack:
                    pack["lastDownloadFailures"] = []
                    CurseForgePackRegistry.save(instance, pack)
                CurseForgeRegistry.save(instance, registry)
                return tuple(warnings)
            last_errors = CurseForgeContentManager._download_round(instance, missing, reporter, round_number)
            if pack:
                pack["lastDownloadFailures"] = [{"path": item["path"], "error": last_errors.get(item["key"], "Download failed")} for item in missing if item["kind"] == "pack"]
                CurseForgePackRegistry.save(instance, pack)
            CurseForgeRegistry.save(instance, registry)

        missing = CurseForgeContentManager._check_all(instance, pack_entries, mod_entries, reporter, CurseForgeContentManager.MAX_DOWNLOAD_ROUNDS + 1)
        if not missing:
            return tuple(warnings)
        lines = []
        for item in missing:
            error = last_errors.get(item["key"], "File is still missing or invalid")
            lines.append(f"- {item['path']}: {error}")
        message = "Required CurseForge files are still missing after 3 download rounds:\n" + "\n".join(lines[:20])
        if len(lines) > 20:
            message += f"\n- ... and {len(lines) - 20} more"
        if block_launch_on_failure:
            raise RuntimeError(message + "\nDisable the managed-file launch block in Instance Settings only if you will install these files manually.")
        warnings.append(message)
        return tuple(warnings)

    @staticmethod
    def _check_all(instance: Instance, pack_entries: list[dict], mod_entries: list[dict], reporter: ProgressReporter | None, round_number: int) -> list[dict]:
        combined: list[dict] = []
        for entry in pack_entries:
            combined.append(CurseForgeContentManager._item(entry, "pack"))
        for entry in mod_entries:
            combined.append(CurseForgeContentManager._item(entry, "mod"))
        total = len(combined)
        missing: list[dict] = []
        message = "Checking CurseForge files..." if round_number == 1 else f"Checking CurseForge files after round {round_number - 1}/3..."
        if reporter is not None:
            reporter.files(stage=ProgressStage.CHECKING_MODS, message=message, current=0, total=total)
        for index, item in enumerate(combined, start=1):
            path = Path(instance.instance_dir) / item["path"]
            valid = path.is_file() and CurseForgeContentManager._verify(path, item["sha1"], item["size"])
            item["entry"]["pendingDownload"] = not valid
            item["entry"]["lastDownloadError"] = "" if valid else str(item["entry"].get("lastDownloadError") or "File is missing or invalid")
            if not valid:
                missing.append(item)
            if reporter is not None:
                reporter.files(stage=ProgressStage.CHECKING_MODS, message=message, current=index, total=total)
        return missing

    @staticmethod
    def _download_round(instance: Instance, missing: list[dict], reporter: ProgressReporter | None, round_number: int) -> dict[str, str]:
        errors: dict[str, str] = {}
        message = f"Downloading missing CurseForge files (round {round_number}/3)..."
        if reporter is not None:
            reporter.files(stage=ProgressStage.DOWNLOADING_MODS, message=message, current=0, total=len(missing))

        def download(item: dict) -> tuple[dict, Path]:
            entry = item["entry"]
            project_id = int(entry.get("projectId") or 0)
            file_id = int(entry.get("fileId") or 0)
            file = CurseForgeClient.get_file(project_id, file_id, force_refresh=not bool(entry.get("downloadUrl")))
            cache = Paths.curseforge_file_cache(project_id, file_id, file.file_name)
            CurseForgeDownloader.download_file(file, cache, reporter=None)
            return item, cache

        completed = 0
        with ThreadPoolExecutor(max_workers=min(CurseForgeContentManager.MAX_WORKERS, max(1, len(missing)))) as executor:
            futures = {executor.submit(download, item): item for item in missing}
            for future in as_completed(futures):
                item = futures[future]
                entry = item["entry"]
                try:
                    _, cache = future.result()
                    added = ModManager.add_mods(instance, [cache], replace=True)
                    if not added:
                        raise RuntimeError("Downloaded file could not be added to the instance.")
                    entry["fileName"] = added[0].file_name
                    entry["path"] = f"mods/{added[0].file_name}"
                    entry["pendingDownload"] = False
                    entry["lastDownloadError"] = ""
                except Exception as error:
                    if is_download_paused(error):
                        raise
                    entry["pendingDownload"] = True
                    entry["lastDownloadError"] = str(error)
                    errors[item["key"]] = str(error)
                completed += 1
                if reporter is not None:
                    reporter.files(stage=ProgressStage.DOWNLOADING_MODS, message=message, current=completed, total=len(missing))
        return errors

    @staticmethod
    def _item(entry: dict, kind: str) -> dict:
        filename = Path(str(entry.get("fileName") or "")).name
        path = str(entry.get("path") or f"mods/{filename}").replace("\\", "/").lstrip("/")
        key = f"{kind}:{entry.get('projectId')}:{entry.get('fileId')}"
        return {"kind": kind, "key": key, "path": path, "sha1": str(entry.get("sha1") or "").lower(), "size": max(0, int(entry.get("size", 0) or 0)), "entry": entry}

    @staticmethod
    def _verify(path: Path, sha1: str, size: int) -> bool:
        try:
            if size > 0 and path.stat().st_size != size:
                return False
        except OSError:
            return False
        if sha1:
            from src.core.network.httpx_downloader import HttpDownloader
            return HttpDownloader.verify_sha1(path, sha1)
        return path.is_file()
