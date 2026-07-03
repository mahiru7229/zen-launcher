from pathlib import Path
from src.models.minecraft.version import Version
from src.models.minecraft.assets import DownloadAsset
from src.models.instance.instance import Instance
import json
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Paths:
    CACHE_ROOT = PROJECT_ROOT / "cache" # place that saves minecraft contents
    INSTANCES_ROOT = PROJECT_ROOT / "instances"


    @staticmethod
    def instance_settings_path(instance:Instance) -> Path:
        instance_settings_path = Paths.INSTANCES_ROOT / instance.name / "settings.json"
        if not instance_settings_path.exists():
            Paths.instance_settings_create(instance)
        return instance_settings_path
        


    @staticmethod
    def instance_settings_create(instance:Instance) -> Path:
        """
        Default settings.
        """
        instance_settings_path = Paths.INSTANCES_ROOT / instance.name / "settings.json"
        settings = {
            "java": {
                "path": "",
                "min_memory": 1024,
                "max_memory": 2048,
                "arguments": []
            },

            "window": {
                "width": 1280,
                "height": 720,
                "fullscreen": False
            },

            "launch": {
                "game_arguments": []
            }
}
        instance_settings_path.write_text(json.dumps(settings, indent=4),encoding="utf-8")
        return instance_settings_path


    @staticmethod
    def instances_root() -> Path:
        instance_dir = Paths.INSTANCES_ROOT
        instance_dir.mkdir(parents=True, exist_ok=True)
        return instance_dir
    
    @staticmethod
    def load_instance_dir(instance_name:str) -> Path:
        instance_dir = Paths.INSTANCES_ROOT / instance_name
        instance_dir.mkdir(parents=True, exist_ok=True)
        return instance_dir
    
    @staticmethod
    def instance_data_path_create():
        instance_path = Paths.instances_root() / "instances.json"
        instance_path.write_text(json.dumps({"instances":[]}, indent=4),encoding="utf-8")
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
        return Paths.version_dir(version) / f"{version.id}.jar"

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

