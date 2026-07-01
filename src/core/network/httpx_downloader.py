from pathlib import Path
from src.models.minecraft.download import DownloadClient
import httpx
import hashlib

CHUNK_SIZE = 64*1024


class HttpDownloader:

    _client: httpx.Client | None = None

    @classmethod
    def get_client(cls) -> httpx.Client:

        if cls._client is None or cls._client.is_closed:
            # cls._client = httpx.Client(http2=True)
            cls._client = httpx.Client()
        return cls._client

    @classmethod
    def close_client(cls) -> None:

        if cls._client and not cls._client.is_closed:
            cls._client.close()
            cls._client = None

    @staticmethod
    def download(client_obj:DownloadClient, client_path:Path, max_retry:int = 2, timeout:float = 20.0) -> Path | None:
        try:
            return HttpDownloader._download_and_verify(client_obj,client_path,max_retry, timeout)

        except RuntimeError:
            return None

    @staticmethod
    def _download_stream(url:str, path:Path, timeout:float) -> None:
        """
        url: link
        path: where you saving this file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        

        client = HttpDownloader.get_client()
        with client.stream("GET", url, timeout=timeout) as response:
            response.raise_for_status()
            with path.open("wb") as file:
                for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                    file.write(chunk)
                    
    @staticmethod
    def verify_sha1(path:Path, expected_sha1:str) -> bool:
        sha1 = hashlib.sha1()
        with path.open("rb") as file:
            while chunk := file.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest() == expected_sha1
        
    @staticmethod
    def delete_file(file:Path) -> None:
        file.unlink(missing_ok=True)
        
    @staticmethod
    def _download_and_verify(download_info:DownloadClient, client_path:Path, max_retry:int,timeout:float) -> Path:
        for _ in range(max_retry):
            try:
                HttpDownloader._download_stream(download_info.url, client_path, timeout)

                if HttpDownloader.verify_sha1(client_path,download_info.sha1):
                    return client_path

                HttpDownloader.delete_file(client_path)
            except (httpx.HTTPError,OSError) as e:
                print(e)
                HttpDownloader.delete_file(client_path)

        raise RuntimeError("Cannot download!:")