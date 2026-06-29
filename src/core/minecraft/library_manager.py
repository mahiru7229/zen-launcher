from src.models.minecraft.version import Version
from src.models.minecraft.library import DownloadLibrary
from src.core.network.httpx_downloader import HttpDownloader
from pathlib import Path
from src.core.fs.paths import Paths
import hashlib
import httpx
import json

class DownloadLibraryManager:

    @staticmethod
    def load(version: Version) -> Path:
        library_data = DownloadLibraryManager._load_download(version.path)
        library_list = DownloadLibraryManager._load_download_object(library_data)

        libraries_dir = Paths.libraries()
        libraries_dirs = []
        for library in library_list:

            library_path = libraries_dir / library.path

            if (
                library_path.exists()
                and HttpDownloader.verify_sha1(
                    library_path,
                    library.sha1,
                )
            ):
                libraries_dirs.append(library_path)
                continue

            HttpDownloader.delete_file(library_path)

            downloaded = HttpDownloader.download(
                library,
                library_path,
            )
            libraries_dirs.append(library_path)
            if downloaded is None:
                raise RuntimeError(
                    f"Cannot download library: {library.path}"
                )

        return libraries_dirs

    @staticmethod
    def _load_download(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def _load_download_object(download_dict:dict) -> list[DownloadLibrary]:
        download_content:list[DownloadLibrary] = []
        for download in download_dict["libraries"]:
            download_content.append(
                DownloadLibrary(
                    url=download["downloads"]["artifact"]["url"],
                    sha1=download["downloads"]["artifact"]["sha1"],
                    size=download["downloads"]["artifact"]["size"],
                    path=Path(download["downloads"]["artifact"]["path"])
                )
            )


        return download_content
        # return DownloadClient(
        #     url= download_dict["downloads"]["client"]["url"],
        #     sha1=download_dict["downloads"]["client"]["sha1"],
        #     size=int(download_dict["downloads"]["client"]["size"])
        # )






    