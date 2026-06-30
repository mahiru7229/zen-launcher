from pathlib import Path
from src.models.minecraft.version import Version
from src.models.minecraft.assets import DownloadAsset

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Paths:
    ROOT = PROJECT_ROOT / "downloads"

    @staticmethod
    def version_dir(version:Version):
        return Paths.ROOT / "versions" / version.id

    @staticmethod
    def client(version:Version):
        return Paths.version_dir(version) / f"{version.id}.jar"

    @staticmethod
    def libraries():
        return Paths.ROOT / "libraries"
    
    
    @staticmethod
    def version_manifest() -> Path:
        return Paths.ROOT / "manifest" / "version_manifest_v2.json"


    @staticmethod
    def version_json(version:Version) -> Path:
        return Paths.version_dir(version) / f"{version.id}.json"
    
    @staticmethod
    def asset_index(version:Version):
        return Paths.ROOT / "assets" / "indexes" / f"{version.assets}.json"
    
    @staticmethod
    def asset_index_dir():
        return Paths.ROOT / "assets" / "objects" 


    @staticmethod
    def asset_object(asset: DownloadAsset):
        directory = Paths.ROOT / "assets" / "objects" / asset.sha1[:2] 
        directory.mkdir(parents=True, exist_ok=True)
        return directory / asset.sha1
    
    @staticmethod
    def assets_dir():
        return Paths.ROOT / "assets" 
    
    @staticmethod
    def natives(version:Version):
        return Paths.ROOT / "downloads" / "natives" / version.id