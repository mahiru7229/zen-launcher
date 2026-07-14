from pathlib import Path
from src.models.minecraft.version import Version
from src.models.minecraft.assets import DownloadAsset
from src.models.instance.instance import Instance
import json
import sys
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Paths:
    CACHE_ROOT = PROJECT_ROOT / "cache" # place that saves minecraft contents
    INSTANCES_ROOT = PROJECT_ROOT / "instances"
    ACCOUNTS_ROOT = PROJECT_ROOT / "accounts"
    CONFIG_ROOT = PROJECT_ROOT / "config"
    THEME_ROOT = PROJECT_ROOT / "themes" 
    INSTANCE_LOCKS_ROOT = INSTANCES_ROOT / ".runtime" / "locks"
    
    @staticmethod
    def initialize() -> None:
        directories = [
            Paths.CACHE_ROOT,
            Paths.INSTANCES_ROOT,
            Paths.ACCOUNTS_ROOT,
            Paths.CONFIG_ROOT,
            Paths.INSTANCE_LOCKS_ROOT,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


    @staticmethod
    def theme_asset(theme: str, *paths: str) -> Path:
        return Paths.theme_dir(theme).joinpath(*paths)

    @staticmethod
    def theme_dir(name:str) -> Path:
        directory  = Path(Paths.THEME_ROOT / name)
        directory.mkdir(parents=True, exist_ok=True)
        """
        Choosing theme pack.
        """
        return directory
    @staticmethod
    def root() -> Path:
        if getattr(sys, "frozen", False):
            # chạy từ exe
            return Path(sys.executable).parent

        # chạy từ source
        return Path(__file__).resolve().parents[3]
    @staticmethod
    def microsoft_config_root()->Path:
        return Paths.CONFIG_ROOT / "microsoft.json"

    @staticmethod
    def account_database_path():
        return Paths.ACCOUNTS_ROOT / "accounts.db"


    @staticmethod
    def accounts_path() -> Path:
        return Paths.ACCOUNTS_ROOT / "accounts.json"




    @staticmethod
    def instance_metadata(instance_name: str) -> Path:
        return Paths.load_instance_dir(instance_name) / "instance.json"




    @staticmethod
    def instance_settings_path(instance:Instance) -> Path:
        instance_settings_path = Path(instance.instance_dir) / "settings.json"
        if not instance_settings_path.exists():
            Paths.instance_settings_create(instance)
        return instance_settings_path
        


    @staticmethod
    def instance_settings_create(instance:Instance) -> Path:
        """
        Default settings.
        """
        instance_settings_path = Path(instance.instance_dir) / "settings.json"
        return instance_settings_path


    @staticmethod
    def instances_root() -> Path:
        instance_dir = Paths.INSTANCES_ROOT
        instance_dir.mkdir(parents=True, exist_ok=True)
        return instance_dir
    
    @staticmethod
    def load_instance_dir(name: str) -> Path:
        return Paths.instances_root() / name


    @staticmethod
    def create_instance_dir(name: str) -> Path:
        path = Paths.load_instance_dir(name)
        path.mkdir(parents=True, exist_ok=False)
        return path
    

    
    @staticmethod
    def instance_data_path_create():
        instance_path = Paths.instances_root() / "instances.json"
        if not instance_path.exists():
            instance_path.write_text(
                json.dumps({"instances": []}, indent=4),
                encoding="utf-8"
            )
        return instance_path
    @staticmethod
    def instance_data_path():
        instance_path = Paths.instances_root() / "instances.json"
        return instance_path

    @staticmethod
    def version_dir(version:Version):
        return Paths.CACHE_ROOT / "versions" / version.id

    @staticmethod
    def client(version:Version):
        raw_json = getattr(version, "raw_json", {}) or {}
        inherited_version = str(raw_json.get("inheritsFrom") or version.id)
        return Paths.CACHE_ROOT / "versions" / inherited_version / f"{inherited_version}.jar"

    @staticmethod
    def fabric_version_dir(game_version: str, loader_version: str) -> Path:
        profile_id = f"fabric-loader-{loader_version}-{game_version}"
        return Paths.CACHE_ROOT / "versions" / profile_id

    @staticmethod
    def fabric_version_json(game_version: str, loader_version: str) -> Path:
        directory = Paths.fabric_version_dir(game_version, loader_version)
        return directory / f"{directory.name}.json"

    @staticmethod
    def instance_mods_dir(instance: Instance) -> Path:
        directory = Path(instance.instance_dir) / "mods"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def libraries():
        return Paths.CACHE_ROOT / "libraries"
    
    
    @staticmethod
    def version_manifest() -> Path:
        return Paths.CACHE_ROOT / "manifest" / "version_manifest_v2.json"


    @staticmethod
    def version_json(version:Version) -> Path:
        return Paths.version_dir(version) / f"{version.id}.json"
    
    @staticmethod
    def asset_index(version:Version):
        return Paths.CACHE_ROOT / "assets" / "indexes" / f"{version.assets}.json"
    
    @staticmethod
    def asset_index_dir():
        return Paths.CACHE_ROOT / "assets" / "objects" 


    @staticmethod
    def asset_object(asset: DownloadAsset):
        directory = Paths.CACHE_ROOT / "assets" / "objects" / asset.sha1[:2] 
        directory.mkdir(parents=True, exist_ok=True)
        return directory / asset.sha1
    
    @staticmethod
    def assets_dir():
        return Paths.CACHE_ROOT / "assets" 
    
    @staticmethod
    def natives(version:Version):
        return Paths.CACHE_ROOT / "natives" / version.id