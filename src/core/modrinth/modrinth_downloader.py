from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import hashlib
import time

import httpx

from src.config import MODRINTH_USER_AGENT
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.network.httpx_downloader import CHUNK_SIZE, HttpDownloader
from src.core.progress.download_rate_meter import DownloadRateMeter
from src.core.progress.progress_reporter import ProgressReporter
from src.models.modrinth.version import ModrinthFile
from src.models.progress.progress_stage import ProgressStage


class _ResumableDownloadError(RuntimeError):
    pass


class ModrinthDownloader:
    ALLOWED_PACK_HOSTS = {
        "cdn.modrinth.com",
        "github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com",
        "github-releases.githubusercontent.com",
        "gitlab.com",
        "assets.gitlab-static.net",
        "maven.fabricmc.net",
        "repo1.maven.org",
    }
    RETRYABLE_STATUS_CODES = HttpDownloader.RETRYABLE_STATUS_CODES
    DEFAULT_TIMEOUT = httpx.Timeout(connect=20.0, read=90.0, write=30.0, pool=30.0)

    @staticmethod
    def download_file(file: ModrinthFile, destination: Path, force: bool = False, reporter: ProgressReporter | None = None, progress_stage: ProgressStage = ProgressStage.DOWNLOADING_MODS, progress_message: str | None = None, max_retry: int = 5) -> Path:
        return ModrinthDownloader.download_urls(urls=(file.url,), destination=destination, sha1=file.sha1, sha512=file.sha512, expected_size=file.size, force=force, restrict_hosts=False, max_retry=max_retry, reporter=reporter, progress_stage=progress_stage, progress_message=progress_message)

    @staticmethod
    def download_urls(urls: tuple[str, ...] | list[str], destination: Path, sha1: str = "", sha512: str = "", expected_size: int = 0, force: bool = False, restrict_hosts: bool = True, max_retry: int = 5, reporter: ProgressReporter | None = None, progress_stage: ProgressStage = ProgressStage.DOWNLOADING_MODS, progress_message: str | None = None) -> Path:
        normalized_urls = tuple(dict.fromkeys(str(url).strip() for url in urls if str(url).strip()))
        if not normalized_urls:
            raise RuntimeError(f"No download URL is available for '{destination.name}'.")
        if not sha1 and not sha512:
            raise RuntimeError(f"No checksum is available for '{destination.name}'.")
        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")

        path_lock = HttpDownloader._get_path_lock(destination)
        with path_lock:
            return ModrinthDownloader._download_locked(normalized_urls, destination, sha1, sha512, max(0, expected_size), force, restrict_hosts, max_retry, reporter, progress_stage, progress_message)

    @staticmethod
    def _download_locked(urls: tuple[str, ...], destination: Path, sha1: str, sha512: str, expected_size: int, force: bool, restrict_hosts: bool, max_retry: int, reporter: ProgressReporter | None, progress_stage: ProgressStage, progress_message: str | None) -> Path:
        message = progress_message or f"Downloading {destination.name}..."
        if destination.is_file() and not force and ModrinthDownloader.verify(destination, sha1=sha1, sha512=sha512, expected_size=expected_size):
            size = expected_size if expected_size > 0 else destination.stat().st_size
            ModrinthDownloader._report(reporter, progress_stage, message, size, size)
            return destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            destination.unlink(missing_ok=True)
        temp = destination.with_name(destination.name + ".part")
        if force:
            temp.unlink(missing_ok=True)

        if temp.is_file() and ModrinthDownloader.verify(temp, sha1=sha1, sha512=sha512, expected_size=expected_size):
            temp.replace(destination)
            final_size = expected_size if expected_size > 0 else destination.stat().st_size
            ModrinthDownloader._report(reporter, progress_stage, message, final_size, final_size)
            return destination

        last_error: Exception | None = None
        last_url = ""

        for url in urls:
            last_url = url
            if restrict_hosts:
                try:
                    ModrinthDownloader._validate_pack_url(url)
                except RuntimeError as error:
                    last_error = error
                    continue

            for attempt in range(1, max_retry + 1):
                response: httpx.Response | None = None
                try:
                    size, actual_sha1, actual_sha512, response = ModrinthDownloader._download_attempt(url, temp, expected_size, reporter, progress_stage, message)
                    ModrinthDownloader._validate_digest(temp.name, size, actual_sha1, actual_sha512, sha1, sha512, expected_size)
                    temp.replace(destination)
                    final_size = expected_size if expected_size > 0 else size
                    ModrinthDownloader._report(reporter, progress_stage, message, final_size, final_size)
                    return destination
                except httpx.HTTPStatusError as error:
                    last_error = error
                    if error.response.status_code not in ModrinthDownloader.RETRYABLE_STATUS_CODES:
                        break
                    if attempt < max_retry:
                        time.sleep(HttpDownloader._retry_delay(attempt, error.response))
                except _ResumableDownloadError as error:
                    last_error = error
                    if attempt < max_retry:
                        time.sleep(HttpDownloader._retry_delay(attempt, response))
                except (httpx.HTTPError, OSError) as error:
                    last_error = error
                    if attempt < max_retry:
                        time.sleep(HttpDownloader._retry_delay(attempt, response))
                except RuntimeError as error:
                    last_error = error
                    temp.unlink(missing_ok=True)
                    if attempt < max_retry:
                        time.sleep(HttpDownloader._retry_delay(attempt, response))

        host = urlparse(last_url).hostname or "unknown host"
        reason = HttpDownloader._describe_error(last_error)
        raise RuntimeError(f"Failed to download '{destination.name}' from all available sources. Last source: {host}. Last error: {reason}") from last_error

    @staticmethod
    def _download_attempt(url: str, temp: Path, expected_size: int, reporter: ProgressReporter | None, progress_stage: ProgressStage, message: str) -> tuple[int, str, str, httpx.Response]:
        force_full_request = False

        while True:
            if force_full_request:
                temp.unlink(missing_ok=True)
            existing_size, sha1_hash, sha512_hash = ModrinthDownloader._hash_partial(temp, expected_size)
            headers = {"User-Agent": MODRINTH_USER_AGENT, "Accept": "application/octet-stream", "Accept-Encoding": "identity"}
            if existing_size > 0:
                headers["Range"] = f"bytes={existing_size}-"

            client = HttpDownloader.get_client()
            with client.stream("GET", url, headers=headers, timeout=ModrinthDownloader.DEFAULT_TIMEOUT) as response:
                status_code = response.status_code

                if status_code == 416 and existing_size > 0 and not force_full_request:
                    force_full_request = True
                    continue

                response.raise_for_status()
                append = existing_size > 0 and status_code == 206

                if status_code == 206 and not HttpDownloader._valid_content_range(response, existing_size if append else 0, expected_size):
                    if existing_size > 0 and not force_full_request:
                        force_full_request = True
                        continue
                    raise RuntimeError(f"Invalid HTTP range response for '{temp.name}'.")

                if not append:
                    existing_size = 0
                    sha1_hash = hashlib.sha1()
                    sha512_hash = hashlib.sha512()

                content_length = HttpDownloader._content_length(response, 0)
                range_total = HttpDownloader._content_range_total(response)
                total = expected_size or range_total or (existing_size + content_length if append else content_length)
                downloaded = existing_size
                response_bytes = 0
                last_percentage = -1
                rate_meter = DownloadRateMeter(downloaded)
                ModrinthDownloader._report(reporter, progress_stage, message, downloaded, total)

                with temp.open("ab" if append else "wb") as output:
                    for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                        if not chunk:
                            continue
                        download_bandwidth_limiter.throttle(len(chunk))
                        output.write(chunk)
                        sha1_hash.update(chunk)
                        sha512_hash.update(chunk)
                        downloaded += len(chunk)
                        response_bytes += len(chunk)

                        if expected_size > 0 and downloaded > expected_size:
                            raise RuntimeError(f"Downloaded file '{temp.name}' is larger than expected.")
                        if total <= 0:
                            continue
                        percentage = min(int(downloaded * 100 / total), 100)
                        if percentage == last_percentage:
                            continue
                        last_percentage = percentage
                        ModrinthDownloader._report(reporter, progress_stage, message, downloaded, total, rate_meter.update(downloaded))

                if content_length > 0 and response_bytes != content_length:
                    raise _ResumableDownloadError(f"Incomplete HTTP response for '{temp.name}': received {response_bytes} of {content_length} bytes.")
                if expected_size > 0 and downloaded < expected_size:
                    raise _ResumableDownloadError(f"Incomplete file '{temp.name}': received {downloaded} of {expected_size} bytes.")
                return downloaded, sha1_hash.hexdigest(), sha512_hash.hexdigest(), response

    @staticmethod
    def _hash_partial(path: Path, expected_size: int) -> tuple[int, hashlib._Hash, hashlib._Hash]:
        sha1_hash = hashlib.sha1()
        sha512_hash = hashlib.sha512()
        if not path.is_file():
            return 0, sha1_hash, sha512_hash

        try:
            size = path.stat().st_size
            if expected_size > 0 and size > expected_size:
                path.unlink(missing_ok=True)
                return 0, sha1_hash, sha512_hash
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    sha1_hash.update(chunk)
                    sha512_hash.update(chunk)
            return size, sha1_hash, sha512_hash
        except OSError:
            path.unlink(missing_ok=True)
            return 0, hashlib.sha1(), hashlib.sha512()

    @staticmethod
    def verify(path: Path, sha1: str = "", sha512: str = "", expected_size: int = 0) -> bool:
        if not path.is_file():
            return False
        if expected_size > 0:
            try:
                if path.stat().st_size != expected_size:
                    return False
            except OSError:
                return False

        if not sha1 and not sha512:
            return False
        sha1_hash = hashlib.sha1() if sha1 else None
        sha512_hash = hashlib.sha512() if sha512 else None
        try:
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    if sha1_hash is not None:
                        sha1_hash.update(chunk)
                    if sha512_hash is not None:
                        sha512_hash.update(chunk)
        except OSError:
            return False
        if sha1_hash is not None and sha1_hash.hexdigest().lower() != sha1.lower():
            return False
        if sha512_hash is not None and sha512_hash.hexdigest().lower() != sha512.lower():
            return False
        return True

    @staticmethod
    def _validate_digest(name: str, size: int, actual_sha1: str, actual_sha512: str, expected_sha1: str, expected_sha512: str, expected_size: int) -> None:
        if expected_size > 0 and size != expected_size:
            raise RuntimeError(f"Size mismatch for '{name}'.")
        if expected_sha1 and actual_sha1.lower() != expected_sha1.lower():
            raise RuntimeError(f"SHA-1 mismatch for '{name}'.")
        if expected_sha512 and actual_sha512.lower() != expected_sha512.lower():
            raise RuntimeError(f"SHA-512 mismatch for '{name}'.")

    @staticmethod
    def _validate_pack_url(url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme.lower() != "https":
            raise RuntimeError("Modpack files must use HTTPS URLs.")
        if not host or parsed.username or parsed.password:
            raise RuntimeError("Modpack download URL is invalid.")
        if host not in ModrinthDownloader.ALLOWED_PACK_HOSTS:
            raise RuntimeError(f"Modpack download host is not allowed: {host}")

    @staticmethod
    def _report(reporter: ProgressReporter | None, stage: ProgressStage, message: str, current: int, total: int, bytes_per_second: float | None = None) -> None:
        if reporter is None:
            return
        reporter.bytes(stage=stage, message=message, current=max(0, current), total=max(0, total), bytes_per_second=bytes_per_second)
