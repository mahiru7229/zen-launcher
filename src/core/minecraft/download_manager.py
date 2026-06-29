from src.models.minecraft.version import Version
from src.models.minecraft.download import DownloadClient
from src.core.network.httpx_downloader import HttpDownloader
from pathlib import Path
from src.core.fs.paths import Paths
import hashlib
import httpx
import json

class DownloadClientManager:

    @staticmethod
    def load(version: Version) -> Path:
        client_data = DownloadClientManager._load_download(version.path)
        client_obj = DownloadClientManager._load_download_object(client_data)

        client_dir = Paths.version_dir(version)
        client_dir.mkdir(parents=True, exist_ok=True)

        client_path = Paths.client(version)

        if (
            client_path.exists()
            and HttpDownloader.verify_sha1(client_path, client_obj.sha1)
        ):
            return client_path

        if client_path.exists():
            HttpDownloader.delete_file(client_path)

        downloaded = HttpDownloader.download(
            client_obj,
            client_path,
        )

        if downloaded is not None:
            return downloaded

        raise RuntimeError("Cannot download client.jar")


    @staticmethod
    def _load_download(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def _load_download_object(download_dict:dict) -> DownloadClient:
        return DownloadClient(
            url= download_dict["downloads"]["client"]["url"],
            sha1=download_dict["downloads"]["client"]["sha1"],
            size=int(download_dict["downloads"]["client"]["size"])
        )






    