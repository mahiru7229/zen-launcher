
from pathlib import Path
import concurrent.futures
import json
import zipfile

from src.core.fs.paths import Paths
from src.core.minecraft.library_rule_manager import LibraryRuleManager
from src.core.network.httpx_downloader import HttpDownloader
from src.core.progress.file_batch_progress import FileBatchProgress
from src.core.progress.progress_reporter import ProgressReporter
from src.models.minecraft.library import DownloadLibrary
from src.models.minecraft.version import Version
from src.models.progress.progress_stage import ProgressStage


MAX_WORKERS = 20


class DownloadLibraryManager:

    @staticmethod
    def load(
        version: Version,
        reporter: ProgressReporter | None = None,
    ) -> list[Path]:
        library_data = DownloadLibraryManager._load_download(
            version.path
        )

        libraries = DownloadLibraryManager._load_download_object(
            library_data
        )

        downloaded_paths: list[Path] = []

        total = len(libraries)

        batch_progress = FileBatchProgress(reporter=reporter, stage=ProgressStage.DOWNLOADING_LIBRARIES, message="Preparing Minecraft libraries...", total=total)
        batch_progress.start()

        if total == 0:
            return downloaded_paths

        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            ) as executor:
                future_to_library = {}
                for library in libraries:
                    token = object()
                    child_reporter = batch_progress.reporter_for(token)
                    future = executor.submit(DownloadLibraryManager._download_single_library, library, version) if child_reporter is None else executor.submit(DownloadLibraryManager._download_single_library, library, version, child_reporter)
                    future_to_library[future] = (library, token)

                for future in concurrent.futures.as_completed(
                    future_to_library
                ):
                    library, token = future_to_library[future]

                    try:
                        library_path = future.result()
                        downloaded_paths.append(library_path)

                    except Exception as error:
                        batch_progress.discard(token)
                        raise RuntimeError(
                            "Failed to download library: "
                            f"{library.path}"
                        ) from error

                    batch_progress.complete(token)

        finally:
            HttpDownloader.close_client()

        return downloaded_paths

    @staticmethod
    def _download_single_library(
        library: DownloadLibrary,
        version: Version,
        reporter: ProgressReporter | None = None,
    ) -> Path:
        library_path = Paths.libraries() / library.path

        if (
            library_path.exists()
            and HttpDownloader.verify_sha1(
                library_path,
                library.sha1,
            )
        ):
            if library.is_native:
                DownloadLibraryManager._extract_native(
                    native_path=library_path,
                    version=version,
                    sha1=library.sha1,
                )

            return library_path

        HttpDownloader.delete_file(library_path)

        kwargs = {"download_info": library, "path": library_path, "max_retry": 5}
        if reporter is not None:
            kwargs.update({"reporter": reporter, "progress_stage": ProgressStage.DOWNLOADING_LIBRARIES, "progress_message": f"Downloading library {library_path.name}..."})
        downloaded_path = HttpDownloader.download(**kwargs)

        if library.is_native:
            DownloadLibraryManager._extract_native(
                native_path=downloaded_path,
                version=version,
                sha1=library.sha1,
            )

        return downloaded_path

    @staticmethod
    def _load_download(path: Path) -> dict:
        try:
            return json.loads(
                path.read_text(encoding="utf-8")
            )

        except (
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            return {}

    @staticmethod
    def _extract_native(
        native_path: Path,
        version: Version,
        sha1: str,
    ) -> None:
        destination = Paths.natives(version)
        marker_dir = destination / ".extracted"
        marker_path = marker_dir / sha1

        if marker_path.exists():
            return

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        marker_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with zipfile.ZipFile(native_path, "r") as archive:
            for member in archive.infolist():
                if member.filename.startswith("META-INF/"):
                    continue

                archive.extract(
                    member,
                    destination,
                )

        marker_path.touch()

    @staticmethod
    def _load_download_object(
        download_dict: dict,
    ) -> list[DownloadLibrary]:
        libraries: list[DownloadLibrary] = []

        for download in download_dict.get(
            "libraries",
            [],
        ):
            if not LibraryRuleManager.is_allowed(download):
                continue

            downloads = download.get(
                "downloads",
                {},
            )

            artifact = downloads.get("artifact")

            if artifact:
                libraries.append(
                    DownloadLibrary(
                        url=artifact["url"],
                        sha1=artifact["sha1"],
                        size=int(artifact["size"]),
                        path=Path(artifact["path"]),
                        is_native=False,
                    )
                )

            native_name = download.get(
                "natives",
                {},
            ).get("windows")

            if not native_name:
                continue

            native_name = native_name.replace(
                "${arch}",
                "64",
            )

            native_artifact = downloads.get(
                "classifiers",
                {},
            ).get(native_name)

            if not native_artifact:
                continue

            libraries.append(
                DownloadLibrary(
                    url=native_artifact["url"],
                    sha1=native_artifact["sha1"],
                    size=int(native_artifact["size"]),
                    path=Path(native_artifact["path"]),
                    is_native=True,
                )
            )

        return libraries

