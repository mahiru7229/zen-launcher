from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.network.httpx_downloader import HttpDownloader
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.file import CurseForgeFile
from src.models.progress.progress_stage import ProgressStage


class CurseForgeDownloader:
    @staticmethod
    def download_file(file: CurseForgeFile, destination: Path, reporter: ProgressReporter | None = None, stage: ProgressStage = ProgressStage.DOWNLOADING_MODS, message: str | None = None) -> Path:
        resolved = file
        if not resolved.is_available:
            raise RuntimeError(
                f"CurseForge file {resolved.file_id} is not available for third-party distribution. "
                f"Open project {resolved.project_id} in CurseForge and place '{resolved.file_name}' manually."
            )
        if not resolved.download_url:
            resolved = replace(resolved, download_url=CurseForgeClient.get_download_url(resolved.project_id, resolved.file_id, force_refresh=True))
        if not resolved.download_url:
            raise RuntimeError(
                f"CurseForge file {resolved.file_id} cannot be downloaded automatically. Open project {resolved.project_id} in CurseForge and place '{resolved.file_name}' manually."
            )
        if not resolved.sha1:
            raise RuntimeError(f"CurseForge file '{resolved.file_name}' does not provide a SHA-1 hash.")
        return HttpDownloader.download(resolved, destination, max_retry=5, timeout=60.0, reporter=reporter, progress_stage=stage, progress_message=message or f"Downloading {resolved.file_name}...")
