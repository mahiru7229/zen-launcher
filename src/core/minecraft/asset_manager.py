from src.core.fs.paths import Paths
from src.models.minecraft.version import Version
from src.core.minecraft.asset_index_manager import AssetIndexManager
from pathlib import Path
from src.models.minecraft.assets import DownloadAsset
from src.core.network.httpx_downloader import HttpDownloader
import json
import concurrent.futures 

MAIN_LINK = "https://resources.download.minecraft.net"
MAX_WORKERS = 10

class AssetManager:
    @staticmethod
    def load(version: Version) -> Path:
        asset_index_path = AssetIndexManager.load(version)
        assets_data = AssetManager._load_asset_index(asset_index_path)

        assets = AssetManager._parse_assets(assets_data)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Giao việc cho các luồng
            futures = [executor.submit(AssetManager._download_single_asset, asset) for asset in assets]
            

            for future in concurrent.futures.as_completed(futures):
                future.result() 


        HttpDownloader.close_client()
        
        return Paths.asset_index_dir()

    @staticmethod
    def _download_single_asset(asset: DownloadAsset) -> None:
        """✨ Hàm mới mình thêm vào để các luồng có thể tự gọi và xử lý từng file"""
        asset_path = Paths.asset_object(asset)
        if (asset_path.exists() and HttpDownloader.verify_sha1(asset_path, asset.sha1)):
            return
            
        HttpDownloader.delete_file(asset_path)
        downloaded = HttpDownloader.download(asset, asset_path, max_retry=5)
        print(f"Current: {asset.logical_name}")
        
        if downloaded is None:
            raise RuntimeError(f"Cannot download asset: {asset.logical_name}\n({asset.sha1})")

    @staticmethod
    def _load_asset_index(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _parse_assets(assets_data:dict) -> list[DownloadAsset]:
        assets:list[DownloadAsset]  = []
        for logical_name,obj in assets_data["objects"].items():

            assets.append(DownloadAsset(
                logical_name=logical_name,
                url=AssetManager._build_download_url(obj["hash"]),
                sha1= obj["hash"],
                size = obj["size"]
                ))
        return assets
        
    @staticmethod
    def _build_download_url(asset_hash:str) -> str:
        hash_prefix = asset_hash[:2]
        return f"{MAIN_LINK}/{hash_prefix}/{asset_hash}"