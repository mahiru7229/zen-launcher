from src.models.instance.instance import Instance
from src.core.fs.paths import Paths
from src.models.instance.settings import InstanceSettings
import json


class SettingsManager:

    DEFAULT_SETTINGS = {
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
            "game_arguments": [],
            "offline_multiplayer_enabled": False
        }
    }

    @staticmethod
    def load(instance: Instance) -> InstanceSettings:
        data = SettingsManager._load_instance_settings(instance)
        if not data:
            SettingsManager.save_default(instance)
            data = SettingsManager.DEFAULT_SETTINGS
        return SettingsManager._parse_instance_settings(data)

    @staticmethod
    def save(instance: Instance, settings: InstanceSettings) -> None:
        path = Paths.instance_settings_path(instance)

        path.parent.mkdir(parents=True, exist_ok=True)

        data = SettingsManager._settings_to_dict(settings)

        path.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

    @staticmethod
    def save_default(instance: Instance) -> None:
        path = Paths.instance_settings_path(instance)

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                SettingsManager.DEFAULT_SETTINGS,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    @staticmethod
    def update_memory(instance: Instance, min_memory: int, max_memory: int) -> InstanceSettings:
        settings = SettingsManager.load(instance)

        settings.min_memory = min_memory
        settings.max_memory = max_memory

        SettingsManager.save(instance, settings)

        return settings

    @staticmethod
    def update_java_path(instance: Instance, java_path: str) -> InstanceSettings:
        settings = SettingsManager.load(instance)

        settings.java_path = java_path

        SettingsManager.save(instance, settings)

        return settings

    @staticmethod
    def update_window(instance: Instance, width: int, height: int, fullscreen: bool) -> InstanceSettings:
        settings = SettingsManager.load(instance)

        settings.width = width
        settings.height = height
        settings.fullscreen = fullscreen

        SettingsManager.save(instance, settings)

        return settings

    @staticmethod
    def update_jvm_arguments(instance: Instance, arguments: list[str]) -> InstanceSettings:
        settings = SettingsManager.load(instance)

        settings.jvm_arguments = arguments

        SettingsManager.save(instance, settings)

        return settings

    @staticmethod
    def update_game_arguments(instance: Instance, arguments: list[str]) -> InstanceSettings:
        settings = SettingsManager.load(instance)

        settings.game_arguments = arguments

        SettingsManager.save(instance, settings)

        return settings

    @staticmethod
    def _load_instance_settings(instance: Instance) -> dict:
        try:
            path = Paths.instance_settings_path(instance)
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _parse_instance_settings(data: dict) -> InstanceSettings:
        java = data.get("java", {})
        window = data.get("window", {})
        launch = data.get("launch", {})
        print(data)
        return InstanceSettings(
            java_path=java.get("path", ""),
            min_memory=int(java.get("min_memory", 1024)),
            max_memory=int(java.get("max_memory", 2048)),
            jvm_arguments=java.get("arguments", []),
            game_arguments=launch.get("game_arguments", []),
            width=int(window.get("width", 1280)),
            height=int(window.get("height", 720)),
            fullscreen=bool(window.get("fullscreen", False)),
            offline_multiplayer_enabled=launch.get("offline_multiplayer_enabled",False)
        )

    @staticmethod
    def _settings_to_dict(settings: InstanceSettings) -> dict:
        return {
            "java": {
                "path": settings.java_path,
                "min_memory": settings.min_memory,
                "max_memory": settings.max_memory,
                "arguments": settings.jvm_arguments
            },
            "window": {
                "width": settings.width,
                "height": settings.height,
                "fullscreen": settings.fullscreen
            },
            "launch": {
                "game_arguments": settings.game_arguments,
                "offline_multiplayer_enabled": settings.offline_multiplayer_enabled
            }
        }