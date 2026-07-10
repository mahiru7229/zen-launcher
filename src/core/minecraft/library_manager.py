from pathlib import Path
import concurrent.futures
import json
import platform
import re
from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader
from src.models.minecraft.library import DownloadLibrary
from src.models.minecraft.version import Version
from src.core.minecraft.library_rule_manager import LibraryRuleManager
MAX_WORKERS = 20


class DownloadLibraryManager:

    @staticmethod
    def load(version: Version) -> list[Path]:
        library_data = DownloadLibraryManager._load_download(version.path)
        libraries = DownloadLibraryManager._load_download_object(library_data)

        downloaded_paths: list[Path] = []

        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            ) as executor:

                future_to_library = {
                    executor.submit(
                        DownloadLibraryManager._download_single_library,
                        library,
                        version
                    ): library
                    for library in libraries
                }

                for future in concurrent.futures.as_completed(future_to_library):
                    library = future_to_library[future]

                    try:
                        path = future.result()
                        downloaded_paths.append(path)

                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to download library: {library.path}"
                        ) from e

        finally:
            HttpDownloader.close_client()

        return downloaded_paths

    @staticmethod
    def _download_single_library(library: DownloadLibrary, version: Version) -> Path:
        library_path = Paths.libraries() / library.path

        if library_path.exists() and HttpDownloader.verify_sha1(library_path, library.sha1):
            if library.is_native:
                DownloadLibraryManager._extract_native(library_path, version, library.sha1)

            return library_path

        HttpDownloader.delete_file(library_path)

        downloaded = HttpDownloader.download(
            library,
            library_path,
            max_retry=5
        )

        if downloaded is None:
            raise RuntimeError(
                f"Cannot download library: {library.path}"
            )

        if library.is_native:
                DownloadLibraryManager._extract_native(library_path, version, library.sha1)
        
        return library_path

    @staticmethod
    def _load_download(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _extract_native(native_path: Path, version: Version, sha1: str) -> None:
        import zipfile

        destination = Paths.natives(version)
        marker_dir = destination / ".extracted"
        marker_path = marker_dir / sha1

        if marker_path.exists():
            return

        destination.mkdir(parents=True, exist_ok=True)
        marker_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(native_path, "r") as archive:
            for member in archive.infolist():
                if member.filename.startswith("META-INF/"):
                    continue

                archive.extract(member, destination)

        marker_path.touch()

    @staticmethod
    def _load_download_object(download_dict: dict) -> list[DownloadLibrary]:
        libraries: list[DownloadLibrary] = []

        for download in download_dict.get("libraries", []):
            if not LibraryRuleManager.is_allowed(download):
                continue

            downloads = download.get("downloads", {})

            artifact = downloads.get("artifact")

            if artifact:
                libraries.append(
                    DownloadLibrary(
                        url=artifact["url"],
                        sha1=artifact["sha1"],
                        size=artifact["size"],
                        path=Path(artifact["path"]),
                        is_native=False
                    )
                )

            native_name = download.get("natives", {}).get("windows")

            if not native_name:
                continue

            native_name = native_name.replace("${arch}", "64")

            native_artifact = downloads.get("classifiers", {}).get(native_name)

            if not native_artifact:
                continue

            libraries.append(
                DownloadLibrary(
                    url=native_artifact["url"],
                    sha1=native_artifact["sha1"],
                    size=native_artifact["size"],
                    path=Path(native_artifact["path"]),
                    is_native=True
                )
            )

        return libraries