from src.core.fs.paths import Paths
from pathlib import Path
from src.models.minecraft.assets import DownloadAsset
import json

MAIN_LINK = "https://resources.download.minecraft.net"


class AssetManager:
    @staticmethod
    def load():
        ...



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

    