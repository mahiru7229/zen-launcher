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
    def launcher_settings_path() -> Path:
        return Paths.CONFIG_ROOT / "launcher_settings.json"

    @staticmethod
    def update_root() -> Path:
        directory = Paths.CACHE_ROOT / "updates"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def update_release_cache() -> Path:
        return Paths.update_root() / "releases.json"

    @staticmethod
    def update_download_path(tag_name: str, asset_name: str) -> Path:
        from urllib.parse import quote

        tag = quote(str(tag_name).strip(), safe="") or "unknown-release"
        filename = Path(str(asset_name)).name or "update.zip"
        return Paths.update_root() / "downloads" / tag / filename

    @staticmethod
    def update_staging_root() -> Path:
        directory = Paths.update_root() / "staging"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

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
    def fabric_metadata_root() -> Path:
        return Paths.CACHE_ROOT / "modloaders" / "fabric"

    @staticmethod
    def fabric_catalog_json(game_version: str) -> Path:
        from urllib.parse import quote

        filename = quote(game_version, safe="") or "unknown"
        return Paths.fabric_metadata_root() / "catalogs" / f"{filename}.json"

    @staticmethod
    def fabric_install_metadata_json(game_version: str, loader_version: str) -> Path:
        from urllib.parse import quote

        game = quote(game_version, safe="") or "unknown"
        loader = quote(loader_version, safe="") or "unknown"
        return Paths.fabric_metadata_root() / "install" / game / f"{loader}.json"

    @staticmethod
    def fabric_profile_json(game_version: str, loader_version: str) -> Path:
        from urllib.parse import quote

        game = quote(game_version, safe="") or "unknown"
        loader = quote(loader_version, safe="") or "unknown"
        return Paths.fabric_metadata_root() / "profiles" / game / f"{loader}.json"

    @staticmethod
    def instance_mods_dir(instance: Instance) -> Path:
        directory = Path(instance.instance_dir) / "mods"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def modrinth_root() -> Path:
        directory = Paths.CACHE_ROOT / "content" / "modrinth"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def modrinth_api_cache(cache_key: str) -> Path:
        return Paths.modrinth_root() / "api" / f"{cache_key}.json"

    @staticmethod
    def modrinth_file_cache(project_id: str, version_id: str, filename: str) -> Path:
        from urllib.parse import quote

        project = quote(str(project_id).strip(), safe="") or "unknown-project"
        version = quote(str(version_id).strip(), safe="") or "unknown-version"
        safe_name = Path(str(filename)).name or "download.bin"
        return Paths.modrinth_root() / "files" / project / version / safe_name

    @staticmethod
    def modrinth_pack_cache(project_id: str, version_id: str, filename: str) -> Path:
        return Paths.modrinth_file_cache(project_id, version_id, filename)

    @staticmethod
    def modrinth_staging_root() -> Path:
        directory = Paths.modrinth_root() / "staging"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def modrinth_instance_registry(instance: Instance) -> Path:
        return Path(instance.instance_dir) / ".mcw" / "modrinth.json"

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