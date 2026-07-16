from __future__ import annotations

from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
from typing import Protocol
import hashlib
import re
import time

import httpx

from src.config import MODRINTH_USER_AGENT
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.network.download_pause import DownloadPausedError, download_pause_controller
from src.core.progress.download_rate_meter import DownloadRateMeter
from src.core.progress.progress_reporter import ProgressReporter
from src.models.progress.progress_stage import ProgressStage


CHUNK_SIZE = 512 * 1024


class DownloadInfo(Protocol):
    url: str
    sha1: str
    size: int


@dataclass(frozen=True)
class _DirectDownloadInfo:
    url: str
    size: int = 0
    sha1: str = ""


class HttpDownloader:
    RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
    CONTENT_RANGE_PATTERN = re.compile(r"^bytes\s+(\d+)-(\d+)/(\d+|\*)$", re.IGNORECASE)

    _client: httpx.Client | None = None
    _client_lock = Lock()
    _path_locks: dict[Path, Lock] = {}
    _path_locks_guard = Lock()

    @classmethod
    def get_client(cls) -> httpx.Client:
        with cls._client_lock:
            if cls._client is None or cls._client.is_closed:
                cls._client = httpx.Client(
                    follow_redirects=True,
                    headers={"User-Agent": MODRINTH_USER_AGENT, "Accept-Encoding": "identity"},
                    limits=httpx.Limits(max_connections=40, max_keepalive_connections=20, keepalive_expiry=15.0),
                )
            return cls._client

    @classmethod
    def close_client(cls) -> None:
        with cls._client_lock:
            if cls._client is not None and not cls._client.is_closed:
                cls._client.close()
            cls._client = None

    @classmethod
    def _get_path_lock(cls, path: Path) -> Lock:
        try:
            normalized_path = path.resolve(strict=False)
        except OSError:
            normalized_path = path.absolute()
        with cls._path_locks_guard:
            return cls._path_locks.setdefault(normalized_path, Lock())

    @staticmethod
    def download(download_info: DownloadInfo, path: Path, max_retry: int = 2, timeout: float = 20.0, reporter: ProgressReporter | None = None, progress_stage: ProgressStage | None = None, progress_message: str | None = None) -> Path:
        download_pause_controller.raise_if_requested()
        path_lock = HttpDownloader._get_path_lock(path)
        with path_lock:
            return HttpDownloader._download_and_verify(download_info=download_info, path=path, max_retry=max_retry, timeout=timeout, reporter=reporter, progress_stage=progress_stage, progress_message=progress_message)

    @staticmethod
    def _download_stream(download_info: DownloadInfo, path: Path, timeout: float, reporter: ProgressReporter | None = None, progress_stage: ProgressStage | None = None, progress_message: str | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        expected_size = max(0, int(getattr(download_info, "size", 0) or 0))
        force_full_request = False

        while True:
            download_pause_controller.raise_if_requested()
            existing_size = 0 if force_full_request else HttpDownloader._partial_size(path, expected_size)
            headers = {"Accept": "application/octet-stream", "Accept-Encoding": "identity"}
            if existing_size > 0:
                headers["Range"] = f"bytes={existing_size}-"

            download_pause_controller.raise_if_requested()
            client = HttpDownloader.get_client()
            with client.stream("GET", download_info.url, headers=headers, timeout=timeout) as response:
                status_code = int(getattr(response, "status_code", 200) or 200)

                if status_code == 416 and existing_size > 0 and not force_full_request:
                    HttpDownloader.delete_file(path)
                    force_full_request = True
                    continue

                response.raise_for_status()
                append = existing_size > 0 and status_code == 206

                if status_code == 206 and not HttpDownloader._valid_content_range(response, existing_size if append else 0, expected_size):
                    if existing_size > 0 and not force_full_request:
                        HttpDownloader.delete_file(path)
                        force_full_request = True
                        continue
                    raise RuntimeError(f"Invalid HTTP range response for '{path.name}'.")

                if not append:
                    existing_size = 0

                content_length = HttpDownloader._content_length(response, 0)
                range_total = HttpDownloader._content_range_total(response)
                total_bytes = expected_size or range_total or (existing_size + content_length if append else content_length)
                downloaded_bytes = existing_size
                response_bytes = 0
                last_reported_percentage = -1
                rate_meter = DownloadRateMeter(downloaded_bytes)

                HttpDownloader._report_progress(reporter=reporter, stage=progress_stage, message=progress_message, current=downloaded_bytes, total=total_bytes)

                with path.open("ab" if append else "wb") as file:
                    for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                        download_pause_controller.raise_if_requested()
                        if not chunk:
                            continue
                        download_bandwidth_limiter.throttle(len(chunk))
                        download_pause_controller.raise_if_requested()
                        file.write(chunk)
                        downloaded_bytes += len(chunk)
                        response_bytes += len(chunk)

                        if expected_size > 0 and downloaded_bytes > expected_size:
                            raise RuntimeError(f"Downloaded file '{path.name}' is larger than expected.")
                        if total_bytes <= 0:
                            continue

                        current_percentage = min(int(downloaded_bytes * 100 / total_bytes), 100)
                        if current_percentage == last_reported_percentage:
                            continue
                        last_reported_percentage = current_percentage
                        HttpDownloader._report_progress(reporter=reporter, stage=progress_stage, message=progress_message, current=downloaded_bytes, total=total_bytes, bytes_per_second=rate_meter.update(downloaded_bytes))

                if content_length > 0 and response_bytes != content_length:
                    raise RuntimeError(f"Incomplete HTTP response for '{path.name}': received {response_bytes} of {content_length} bytes.")
                if expected_size > 0 and downloaded_bytes != expected_size:
                    raise RuntimeError(f"Size mismatch for '{path.name}': received {downloaded_bytes} of {expected_size} bytes.")
                if total_bytes > 0 and last_reported_percentage < 100:
                    HttpDownloader._report_progress(reporter=reporter, stage=progress_stage, message=progress_message, current=downloaded_bytes, total=total_bytes, bytes_per_second=rate_meter.update(downloaded_bytes))
                return

    @staticmethod
    def _report_progress(reporter: ProgressReporter | None, stage: ProgressStage | None, message: str | None, current: int, total: int, bytes_per_second: float | None = None) -> None:
        if reporter is None or stage is None:
            return
        reporter.bytes(stage=stage, message=message or "Downloading file...", current=max(0, current), total=max(0, total), bytes_per_second=bytes_per_second)

    @staticmethod
    def calculate_sha1(path: Path) -> str | None:
        if not path.is_file():
            return None
        sha1 = hashlib.sha1(usedforsecurity=False)
        try:
            with path.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    download_pause_controller.raise_if_requested()
                    sha1.update(chunk)
        except OSError:
            return None
        return sha1.hexdigest().lower()

    @staticmethod
    def verify_sha1(path: Path, expected_sha1: str) -> bool:
        if not expected_sha1:
            return False
        actual_sha1 = HttpDownloader.calculate_sha1(path)
        return actual_sha1 is not None and actual_sha1 == expected_sha1.lower()

    @staticmethod
    def download_and_hash(url: str, path: Path, max_retry: int = 2, timeout: float = 20.0, force: bool = False, reporter: ProgressReporter | None = None, progress_stage: ProgressStage | None = None, progress_message: str | None = None) -> tuple[Path, str, int]:
        path_lock = HttpDownloader._get_path_lock(path)
        with path_lock:
            if path.is_file() and not force:
                sha1 = HttpDownloader.calculate_sha1(path)
                if sha1 is not None:
                    return path, sha1, path.stat().st_size
            if max_retry < 1:
                raise ValueError("max_retry must be at least 1")

            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = path.with_name(f"{path.name}.part")
            if force:
                HttpDownloader.delete_file(temp_path)
            info = _DirectDownloadInfo(url=url)
            last_error: Exception | None = None

            for attempt in range(1, max_retry + 1):
                try:
                    HttpDownloader._download_stream(download_info=info, path=temp_path, timeout=timeout, reporter=reporter, progress_stage=progress_stage, progress_message=progress_message)
                    sha1 = HttpDownloader.calculate_sha1(temp_path)
                    if sha1 is None:
                        raise OSError(f"Could not hash downloaded file '{path.name}'.")
                    size = temp_path.stat().st_size
                    temp_path.replace(path)
                    return path, sha1, size
                except DownloadPausedError:
                    raise
                except (httpx.HTTPError, OSError, RuntimeError) as error:
                    last_error = error
                    if not HttpDownloader._should_retry(error, attempt, max_retry):
                        break
                    HttpDownloader._sleep_retry(HttpDownloader._retry_delay(attempt, HttpDownloader._error_response(error)))

            HttpDownloader.delete_file(temp_path)
            raise RuntimeError(f"Failed to download '{path.name}' after {max_retry} attempts: {HttpDownloader._describe_error(last_error)}") from last_error

    @staticmethod
    def _content_length(response: httpx.Response, fallback: int) -> int:
        raw_length = response.headers.get("Content-Length")
        if raw_length is None:
            return fallback
        try:
            return max(0, int(raw_length))
        except ValueError:
            return fallback

    @staticmethod
    def _parse_content_range(response: httpx.Response) -> tuple[int, int, int | None] | None:
        value = str(response.headers.get("Content-Range", "")).strip()
        match = HttpDownloader.CONTENT_RANGE_PATTERN.fullmatch(value)
        if match is None:
            return None
        start = int(match.group(1))
        end = int(match.group(2))
        total = None if match.group(3) == "*" else int(match.group(3))
        if end < start:
            return None
        return start, end, total

    @staticmethod
    def _valid_content_range(response: httpx.Response, expected_start: int, expected_size: int) -> bool:
        parsed = HttpDownloader._parse_content_range(response)
        if parsed is None:
            return False
        start, end, total = parsed
        if start != expected_start:
            return False
        content_length = HttpDownloader._content_length(response, 0)
        if content_length > 0 and end - start + 1 != content_length:
            return False
        if expected_size > 0 and total is not None and total != expected_size:
            return False
        return True

    @staticmethod
    def _content_range_total(response: httpx.Response) -> int:
        parsed = HttpDownloader._parse_content_range(response)
        if parsed is None or parsed[2] is None:
            return 0
        return parsed[2]

    @staticmethod
    def _partial_size(path: Path, expected_size: int) -> int:
        if not path.is_file():
            return 0
        try:
            size = path.stat().st_size
        except OSError:
            HttpDownloader.delete_file(path)
            return 0
        if expected_size > 0 and size > expected_size:
            HttpDownloader.delete_file(path)
            return 0
        return size

    @staticmethod
    def _error_response(error: Exception | None) -> httpx.Response | None:
        if isinstance(error, httpx.HTTPStatusError):
            return error.response
        return None

    @staticmethod
    def _should_retry(error: Exception, attempt: int, max_retry: int) -> bool:
        if attempt >= max_retry:
            return False
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code in HttpDownloader.RETRYABLE_STATUS_CODES
        return True

    @staticmethod
    def _retry_delay(attempt: int, response: httpx.Response | None = None) -> float:
        if response is not None:
            retry_after = str(response.headers.get("Retry-After", "")).strip()
            if retry_after:
                try:
                    return min(max(float(retry_after), 0.0), 30.0)
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(retry_after)
                        return min(max(retry_at.timestamp() - time.time(), 0.0), 30.0)
                    except (TypeError, ValueError, OverflowError):
                        pass
        return float(min(2 ** (attempt - 1), 8))

    @staticmethod
    def _sleep_retry(seconds: float) -> None:
        if download_pause_controller.is_active:
            download_pause_controller.wait(seconds)
            return
        time.sleep(seconds)

    @staticmethod
    def _describe_error(error: Exception | None) -> str:
        if error is None:
            return "unknown error"
        if isinstance(error, httpx.HTTPStatusError):
            return f"HTTP {error.response.status_code} from {error.request.url.host}"
        message = str(error).strip()
        return message or error.__class__.__name__

    @staticmethod
    def delete_file(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _download_and_verify(download_info: DownloadInfo, path: Path, max_retry: int, timeout: float, reporter: ProgressReporter | None = None, progress_stage: ProgressStage | None = None, progress_message: str | None = None) -> Path:
        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")
        if HttpDownloader.verify_sha1(path, download_info.sha1):
            return path

        temp_path = path.with_name(f"{path.name}.part")
        if HttpDownloader.verify_sha1(temp_path, download_info.sha1):
            temp_path.replace(path)
            return path

        last_error: Exception | None = None
        for attempt in range(1, max_retry + 1):
            download_pause_controller.raise_if_requested()
            try:
                HttpDownloader._download_stream(download_info=download_info, path=temp_path, timeout=timeout, reporter=reporter, progress_stage=progress_stage, progress_message=progress_message)
                if not HttpDownloader.verify_sha1(temp_path, download_info.sha1):
                    HttpDownloader.delete_file(temp_path)
                    raise RuntimeError(f"SHA1 mismatch for: {path.name}")
                temp_path.replace(path)
                return path
            except DownloadPausedError:
                raise
            except (httpx.HTTPError, OSError, RuntimeError) as error:
                last_error = error
                if not HttpDownloader._should_retry(error, attempt, max_retry):
                    break
                HttpDownloader._sleep_retry(HttpDownloader._retry_delay(attempt, HttpDownloader._error_response(error)))

        HttpDownloader.delete_file(temp_path)
        raise RuntimeError(f"Failed to download '{path.name}' after {max_retry} attempts: {HttpDownloader._describe_error(last_error)}") from last_error
