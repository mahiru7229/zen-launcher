from src.models.minecraft.version import Version
from src.models.minecraft.download import DownloadClient
from pathlib import Path
import hashlib
import httpx
import json

class DownloadClientManager:

    @staticmethod
    def download_client(version: Version):
        ...
    


    @staticmethod
    def _load_download(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def _load_download_object(download_dict:dict) -> DownloadClient:
        return DownloadClient(
            url= download_dict.downloads["client"]["url"],
            sha1=download_dict.downloads["client"]["sha1"],
            size=int(download_dict.downloads["client"]["size"])
        )

    @staticmethod
    def _check_sha1(path:Path):
        pass




    