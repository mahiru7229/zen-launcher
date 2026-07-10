from pathlib import Path
import concurrent.futures
import json

from src.core.fs.paths import Paths
from src.core.minecraft.asset_index_manager import AssetIndexManager
from src.core.network.httpx_downloader import HttpDownloader
from src.models.minecraft.assets import DownloadAsset
from src.models.minecraft.version import Version

MAIN_LINK = "https://resources.download.minecraft.net"
MAX_WORKERS = 20


class AssetManager:

    @staticmethod
    def load(version: Version) -> Path:
        asset_index_path = AssetIndexManager.load(version)
        assets_data = AssetManager._load_asset_index(asset_index_path)
        assets = AssetManager._parse_assets(assets_data)

        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            ) as executor:

                future_to_asset = {
                    executor.submit(
                        AssetManager._download_single_asset,
                        asset
                    ): asset
                    for asset in assets
                }

                for future in concurrent.futures.as_completed(future_to_asset):
                    asset = future_to_asset[future]

                    try:
                        future.result()
                    except Exception as e:
                            print(type(e))
                            print(e)
                            raise RuntimeError(
                                f"Failed to download asset: {asset.logical_name}"
                            ) from e

        finally:
            HttpDownloader.close_client()

        return Paths.asset_index_dir()

    @staticmethod
    def _download_single_asset(asset: DownloadAsset) -> None:
        asset_path = Paths.asset_object(asset)

        if (
            asset_path.exists()
            and HttpDownloader.verify_sha1(asset_path, asset.sha1)
        ):
            return

        HttpDownloader.delete_file(asset_path)

        downloaded = HttpDownloader.download(
            asset,
            asset_path,
            max_retry=5
        )

        if downloaded is None:
            raise RuntimeError(
                f"Cannot download asset: {asset.logical_name}\n({asset.sha1})"
            )

    @staticmethod
    def _load_asset_index(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _parse_assets(assets_data: dict) -> list[DownloadAsset]:
        assets: list[DownloadAsset] = []

        for logical_name, obj in assets_data.get("objects", {}).items():
            assets.append(
                DownloadAsset(
                    logical_name=logical_name,
                    url=AssetManager._build_download_url(obj["hash"]),
                    sha1=obj["hash"],
                    size=obj["size"],
                )
            )

        return assets

    @staticmethod
    def _build_download_url(asset_hash: str) -> str:
        return f"{MAIN_LINK}/{asset_hash[:2]}/{asset_hash}"