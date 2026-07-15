from pathlib import Path
import time

import httpx

from src.core.java.java_checksum import JavaChecksum
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.network.httpx_downloader import CHUNK_SIZE, HttpDownloader
from src.core.progress.download_rate_meter import DownloadRateMeter
from src.core.progress.progress_reporter import ProgressReporter
from src.models.java.java_release import JavaRelease
from src.models.progress.progress_stage import ProgressStage


class JavaArchiveDownloader:
    @staticmethod
    def download(release: JavaRelease, destination: Path, reporter: ProgressReporter | None = None, max_retry: int = 3, timeout: float = 60.0) -> Path:
        if JavaChecksum.verify_sha256(destination, release.sha256):
            return destination
        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")

        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_name(f"{destination.name}.part")
        last_error: Exception | None = None

        for attempt in range(1, max_retry + 1):
            try:
                temp_path.unlink(missing_ok=True)
                JavaArchiveDownloader._download_stream(release, temp_path, reporter, timeout)
                if not JavaChecksum.verify_sha256(temp_path, release.sha256):
                    raise RuntimeError(f"SHA-256 mismatch for Java {release.major} archive.")
                temp_path.replace(destination)
                return destination
            except (httpx.HTTPError, OSError, RuntimeError) as error:
                last_error = error
                temp_path.unlink(missing_ok=True)
                if attempt < max_retry:
                    time.sleep(min(2 ** (attempt - 1), 8))

        raise RuntimeError(f"Failed to download Java {release.major} after {max_retry} attempts.") from last_error

    @staticmethod
    def _download_stream(release: JavaRelease, destination: Path, reporter: ProgressReporter | None, timeout: float) -> None:
        client = HttpDownloader.get_client()
        with client.stream("GET", release.url, timeout=timeout) as response:
            response.raise_for_status()
            total = JavaArchiveDownloader._content_length(response, release.size)
            downloaded = 0
            last_percentage = -1
            rate_meter = DownloadRateMeter(downloaded)
            JavaArchiveDownloader._report(reporter, release.major, downloaded, total)

            with destination.open("wb") as file:
                for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
                    download_bandwidth_limiter.throttle(len(chunk))
                    file.write(chunk)
                    downloaded += len(chunk)
                    if total <= 0:
                        continue
                    percentage = min(int(downloaded * 100 / total), 100)
                    if percentage == last_percentage:
                        continue
                    last_percentage = percentage
                    JavaArchiveDownloader._report(reporter, release.major, downloaded, total, rate_meter.update(downloaded))

            if total > 0 and downloaded >= total and last_percentage < 100:
                JavaArchiveDownloader._report(reporter, release.major, total, total, rate_meter.update(total))

    @staticmethod
    def _content_length(response: httpx.Response, fallback: int) -> int:
        raw_length = response.headers.get("Content-Length")
        if raw_length is None:
            return fallback
        try:
            return int(raw_length)
        except ValueError:
            return fallback

    @staticmethod
    def _report(reporter: ProgressReporter | None, major: int, current: int, total: int, bytes_per_second: float | None = None) -> None:
        if reporter is None:
            return
        reporter.bytes(stage=ProgressStage.DOWNLOADING_JAVA, message=f"Downloading Java {major}...", current=current, total=total, bytes_per_second=bytes_per_second)
