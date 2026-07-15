from __future__ import annotations

from pathlib import Path
import time

import httpx

from src.core.java.java_checksum import JavaChecksum
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.network.download_pause import DownloadPausedError, download_pause_controller
from src.core.network.httpx_downloader import CHUNK_SIZE, HttpDownloader
from src.core.progress.download_rate_meter import DownloadRateMeter
from src.core.progress.progress_reporter import ProgressReporter
from src.models.java.java_release import JavaRelease
from src.models.progress.progress_stage import ProgressStage


class JavaArchiveDownloader:
    @staticmethod
    def download(release: JavaRelease, destination: Path, reporter: ProgressReporter | None = None, max_retry: int = 3, timeout: float = 60.0) -> Path:
        download_pause_controller.raise_if_requested()
        if JavaChecksum.verify_sha256(destination, release.sha256):
            return destination
        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_name(f"{destination.name}.part")
        if JavaChecksum.verify_sha256(temp_path, release.sha256):
            temp_path.replace(destination)
            return destination

        last_error: Exception | None = None
        for attempt in range(1, max_retry + 1):
            download_pause_controller.raise_if_requested()
            try:
                JavaArchiveDownloader._download_stream(release, temp_path, reporter, timeout)
                if not JavaChecksum.verify_sha256(temp_path, release.sha256):
                    temp_path.unlink(missing_ok=True)
                    raise RuntimeError(f"SHA-256 mismatch for Java {release.major} archive.")
                temp_path.replace(destination)
                return destination
            except DownloadPausedError:
                raise
            except (httpx.HTTPError, OSError, RuntimeError) as error:
                last_error = error
                if attempt < max_retry:
                    delay = min(2 ** (attempt - 1), 8)
                    if download_pause_controller.is_active:
                        download_pause_controller.wait(delay)
                    else:
                        time.sleep(delay)

        temp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download Java {release.major} after {max_retry} attempts.") from last_error

    @staticmethod
    def _download_stream(release: JavaRelease, destination: Path, reporter: ProgressReporter | None, timeout: float) -> None:
        force_full_request = False

        while True:
            download_pause_controller.raise_if_requested()
            if force_full_request:
                destination.unlink(missing_ok=True)
            existing_size = HttpDownloader._partial_size(destination, max(0, int(release.size or 0)))
            headers = {"Accept": "application/octet-stream", "Accept-Encoding": "identity"}
            if existing_size > 0:
                headers["Range"] = f"bytes={existing_size}-"

            client = HttpDownloader.get_client()
            with client.stream("GET", release.url, headers=headers, timeout=timeout) as response:
                status_code = int(response.status_code)
                if status_code == 416 and existing_size > 0 and not force_full_request:
                    force_full_request = True
                    continue

                response.raise_for_status()
                append = existing_size > 0 and status_code == 206
                if status_code == 206 and not HttpDownloader._valid_content_range(response, existing_size if append else 0, release.size):
                    if existing_size > 0 and not force_full_request:
                        force_full_request = True
                        continue
                    raise RuntimeError(f"Invalid HTTP range response for Java {release.major} archive.")

                if not append:
                    existing_size = 0

                content_length = HttpDownloader._content_length(response, 0)
                range_total = HttpDownloader._content_range_total(response)
                total = release.size or range_total or (existing_size + content_length if append else content_length)
                downloaded = existing_size
                response_bytes = 0
                last_percentage = -1
                rate_meter = DownloadRateMeter(downloaded)
                JavaArchiveDownloader._report(reporter, release.major, downloaded, total)

                with destination.open("ab" if append else "wb") as file:
                    for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                        download_pause_controller.raise_if_requested()
                        if not chunk:
                            continue
                        download_bandwidth_limiter.throttle(len(chunk))
                        download_pause_controller.raise_if_requested()
                        file.write(chunk)
                        downloaded += len(chunk)
                        response_bytes += len(chunk)
                        if release.size > 0 and downloaded > release.size:
                            raise RuntimeError(f"Downloaded Java {release.major} archive is larger than expected.")
                        if total <= 0:
                            continue
                        percentage = min(int(downloaded * 100 / total), 100)
                        if percentage == last_percentage:
                            continue
                        last_percentage = percentage
                        JavaArchiveDownloader._report(reporter, release.major, downloaded, total, rate_meter.update(downloaded))

                if content_length > 0 and response_bytes != content_length:
                    raise RuntimeError(f"Incomplete Java {release.major} response: received {response_bytes} of {content_length} bytes.")
                if release.size > 0 and downloaded != release.size:
                    raise RuntimeError(f"Size mismatch for Java {release.major}: received {downloaded} of {release.size} bytes.")
                if total > 0 and last_percentage < 100:
                    JavaArchiveDownloader._report(reporter, release.major, downloaded, total, rate_meter.update(downloaded))
                return

    @staticmethod
    def _report(reporter: ProgressReporter | None, major: int, current: int, total: int, bytes_per_second: float | None = None) -> None:
        if reporter is None:
            return
        reporter.bytes(stage=ProgressStage.DOWNLOADING_JAVA, message=f"Downloading Java {major}...", current=current, total=total, bytes_per_second=bytes_per_second)
