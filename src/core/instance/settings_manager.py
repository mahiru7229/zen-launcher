from src.models.instance.instance import Instance
from src.core.fs.paths import Paths
from src.models.instance.settings import InstanceSettings
import json


class SettingsManager:
    @staticmethod
    def load(instance:Instance) -> InstanceSettings:
        instance_settings_data = SettingsManager._load_instance_settings(instance)
        return SettingsManager._parse_instance_settings(instance_settings_data)


    @staticmethod
    def _load_instance_settings(instance:Instance) -> dict:
        try:
            instance_settings_path = Paths.instance_settings_path(instance)
            return json.loads(instance_settings_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        
    def _parse_instance_settings(instance_data:dict) ->InstanceSettings:
        java = instance_data.get("java")
        window = instance_data.get("window")
        launch = instance_data.get("launch")
        return InstanceSettings(
            java_path=java.get("path"),
            min_memory=int(java.get("min_memory")),
            max_memory=int(java.get("max_memory")),
            jvm_arguments=java.get("arguments"),
            game_arguments=launch.get("game_arguments"),
            width=window.get("width"),
            height=window.get("height"),
            fullscreen=window.get("fullscreen")
        )
