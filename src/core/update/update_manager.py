from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid
import zipfile

from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader
from src.core.update.github_release_client import GitHubReleaseClient
from src.models.update.update_info import PreparedUpdate, UpdateInfo


class UpdateManager:
    MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
    MAX_EXTRACTED_BYTES = 4 * 1024 * 1024 * 1024
    MAX_ARCHIVE_ENTRIES = 20_000

    def __init__(self, repository: str, current_version: str, channel: str = "beta") -> None:
        self.client = GitHubReleaseClient(repository=repository, current_version=current_version, channel=channel)

    def check_for_update(self, force_refresh: bool = False) -> UpdateInfo | None:
        return self.client.check(force_refresh=force_refresh)

    def prepare_update(self, info: UpdateInfo) -> PreparedUpdate:
        archive_path = Paths.update_download_path(info.tag_name, info.asset.name)
        self._download_archive(info, archive_path)

        staging_directory = Paths.update_staging_root() / f"{self._safe_name(info.tag_name)}-{uuid.uuid4().hex}"
        extraction_directory = staging_directory / "extracted"
        try:
            extraction_directory.mkdir(parents=True, exist_ok=False)
            self._extract_archive(archive_path, extraction_directory)
            content_directory = self._resolve_content_directory(extraction_directory)
            if not any(content_directory.iterdir()):
                raise RuntimeError("The update archive does not contain any files.")
            return PreparedUpdate(info=info, archive_path=archive_path, staging_directory=staging_directory, content_directory=content_directory)
        except Exception:
            shutil.rmtree(staging_directory, ignore_errors=True)
            raise

    def _download_archive(self, info: UpdateInfo, archive_path: Path) -> None:
        expected_sha256 = info.asset.sha256
        if archive_path.is_file() and self._archive_matches(archive_path, info.asset.size, expected_sha256):
            return

        archive_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = archive_path.with_name(f"{archive_path.name}.part")
        temporary_path.unlink(missing_ok=True)
        sha256 = hashlib.sha256()
        downloaded = 0

        try:
            client = HttpDownloader.get_client()
            with client.stream(
                "GET",
                info.asset.download_url,
                headers={"User-Agent": f"mahiru7229/mcw-launcher/{info.current_version}"},
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                with temporary_path.open("wb") as file:
                    for chunk in response.iter_bytes(chunk_size=256 * 1024):
                        if not chunk:
                            continue
                        downloaded += len(chunk)
                        if downloaded > self.MAX_ARCHIVE_BYTES:
                            raise RuntimeError("The update archive is larger than the allowed limit.")
                        sha256.update(chunk)
                        file.write(chunk)
                    file.flush()
                    os.fsync(file.fileno())

            if info.asset.size > 0 and downloaded != info.asset.size:
                raise RuntimeError(f"The update download is incomplete ({downloaded} of {info.asset.size} bytes).")
            actual_sha256 = sha256.hexdigest().lower()
            if expected_sha256 is not None and actual_sha256 != expected_sha256.lower():
                raise RuntimeError("The update archive failed SHA-256 verification.")
            temporary_path.replace(archive_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _archive_matches(path: Path, expected_size: int, expected_sha256: str | None) -> bool:
        try:
            if expected_size > 0 and path.stat().st_size != expected_size:
                return False
            if expected_sha256 is None:
                return zipfile.is_zipfile(path)
            sha256 = hashlib.sha256()
            with path.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    sha256.update(chunk)
            return sha256.hexdigest().lower() == expected_sha256.lower()
        except OSError:
            return False

    def _extract_archive(self, archive_path: Path, destination: Path) -> None:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > self.MAX_ARCHIVE_ENTRIES:
                raise RuntimeError("The update archive contains too many files.")

            extracted_size = 0
            for entry in entries:
                if self._is_symlink(entry):
                    raise RuntimeError(f"The update archive contains an unsupported symbolic link: {entry.filename}")
                relative_path = self._safe_archive_path(entry.filename)
                if relative_path is None:
                    continue

                extracted_size += max(0, entry.file_size)
                if extracted_size > self.MAX_EXTRACTED_BYTES:
                    raise RuntimeError("The extracted update is larger than the allowed limit.")

                output_path = destination.joinpath(*relative_path.parts)
                if entry.is_dir():
                    output_path.mkdir(parents=True, exist_ok=True)
                    continue

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry, "r") as source, output_path.open("wb") as target:
                    shutil.copyfileobj(source, target, length=256 * 1024)

    @staticmethod
    def _safe_archive_path(filename: str) -> PurePosixPath | None:
        normalized = str(filename).replace("\\", "/").strip()
        if not normalized:
            return None
        path = PurePosixPath(normalized)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise RuntimeError(f"Unsafe path in update archive: {filename}")
        if path.parts and ":" in path.parts[0]:
            raise RuntimeError(f"Unsafe path in update archive: {filename}")
        return path

    @staticmethod
    def _is_symlink(entry: zipfile.ZipInfo) -> bool:
        mode = entry.external_attr >> 16
        return stat.S_ISLNK(mode)

    @staticmethod
    def _resolve_content_directory(extraction_directory: Path) -> Path:
        children = [child for child in extraction_directory.iterdir() if child.name != "__MACOSX"]
        files = [child for child in children if child.is_file()]
        directories = [child for child in children if child.is_dir()]
        if not files and len(directories) == 1:
            return directories[0]
        return extraction_directory

    @staticmethod
    def _safe_name(value: str) -> str:
        cleaned = "".join(character if character.isalnum() or character in {"-", ".", "_"} else "-" for character in str(value))
        return cleaned.strip("-._") or "update"
