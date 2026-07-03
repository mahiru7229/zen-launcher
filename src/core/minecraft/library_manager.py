from pathlib import Path
import concurrent.futures
import json

from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader
from src.models.minecraft.library import DownloadLibrary
from src.models.minecraft.version import Version

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
                        library
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
    def _download_single_library(library: DownloadLibrary) -> Path:
        library_path = Paths.libraries() / library.path

        if (
            library_path.exists()
            and HttpDownloader.verify_sha1(
                library_path,
                library.sha1
            )
        ):
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

        return library_path

    @staticmethod
    def _load_download(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _load_download_object(
        download_dict: dict
    ) -> list[DownloadLibrary]:

        libraries: list[DownloadLibrary] = []

        for download in download_dict.get("libraries", []):

            artifact = download.get("downloads", {}).get("artifact")

            if artifact is None:
                continue

            libraries.append(
                DownloadLibrary(
                    url=artifact["url"],
                    sha1=artifact["sha1"],
                    size=artifact["size"],
                    path=Path(artifact["path"])
                )
            )

        return libraries