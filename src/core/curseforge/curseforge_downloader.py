from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.network.httpx_downloader import HttpDownloader
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.manual_download import CurseForgeManualDownload
from src.models.progress.progress_stage import ProgressStage


class CurseForgeManualDownloadRequired(RuntimeError):
    def __init__(self, requirement: CurseForgeManualDownload) -> None:
        super().__init__(requirement.reason)
        self.requirement = requirement


class CurseForgeDownloader:
    @staticmethod
    def download_file(file: CurseForgeFile, destination: Path, reporter: ProgressReporter | None = None, stage: ProgressStage = ProgressStage.DOWNLOADING_MODS, message: str | None = None, project_name: str = "") -> Path:
        resolved = file
        if not resolved.download_url and resolved.is_available:
            try:
                download_url = CurseForgeClient.get_download_url(resolved.project_id, resolved.file_id, force_refresh=True)
            except RuntimeError as error:
                if int(getattr(error, "gateway_status", 0) or 0) not in {403, 404}:
                    raise
                download_url = ""
            resolved = replace(resolved, download_url=download_url)
        if not resolved.is_available or not resolved.download_url:
            name = str(project_name).strip() or f"CurseForge project {resolved.project_id}"
            project_url = f"https://www.curseforge.com/minecraft/mc-mods/{resolved.project_id}"
            reason = (
                f"'{name}' cannot be downloaded automatically because its author disabled third-party distribution. "
                f"Download '{resolved.file_name}' from CurseForge and select it in MCW Launcher."
            )
            raise CurseForgeManualDownloadRequired(
                CurseForgeManualDownload(
                    project_id=resolved.project_id,
                    file_id=resolved.file_id,
                    project_name=name,
                    file_name=resolved.file_name,
                    file_size=resolved.file_length,
                    sha1=resolved.sha1,
                    project_url=project_url,
                    reason=reason,
                )
            )
        if not resolved.sha1:
            raise RuntimeError(f"CurseForge file '{resolved.file_name}' does not provide a SHA-1 hash.")
        return HttpDownloader.download(
            resolved,
            destination,
            max_retry=5,
            timeout=60.0,
            reporter=reporter,
            progress_stage=stage,
            progress_message=message or f"Downloading {resolved.file_name}...",
        )
