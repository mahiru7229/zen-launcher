from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

from src.core.fs.paths import Paths
from src.core.system.memory import MemoryAllocationPolicy
from src.models.instance.instance import Instance
from src.models.instance.settings import InstanceSettings


class SettingsManager:
    DEFAULT_SETTINGS = {
        "java": {
            "path": "",
            "min_memory": 1024,
            "max_memory": 2048,
            "arguments": [],
        },
        "window": {
            "width": 1280,
            "height": 720,
            "fullscreen": False,
        },
        "launch": {
            "game_arguments": [],
            "offline_multiplayer_enabled": False,
            "block_launch_on_modrinth_failure": True,
        },
    }

    @staticmethod
    def load(instance: Instance) -> InstanceSettings:
        data = SettingsManager._load_instance_settings(instance)
        if not data:
            SettingsManager.save_default(instance)
            data = copy.deepcopy(SettingsManager.DEFAULT_SETTINGS)
        return SettingsManager._parse_instance_settings(data)

    @staticmethod
    def save(instance: Instance, settings: InstanceSettings) -> None:
        settings.min_memory, settings.max_memory = MemoryAllocationPolicy.normalize(settings.min_memory, settings.max_memory)
        SettingsManager._write(Paths.instance_settings_path(instance), SettingsManager._settings_to_dict(settings))

    @staticmethod
    def save_default(instance: Instance) -> None:
        SettingsManager._write(Paths.instance_settings_path(instance), copy.deepcopy(SettingsManager.DEFAULT_SETTINGS))

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
        path = Paths.instance_settings_path(instance)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Instance settings root must be an object.")
            return data
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, UnicodeError, TypeError, ValueError):
            SettingsManager._backup_broken_file(path)
            return {}
        except OSError:
            return {}

    @staticmethod
    def _parse_instance_settings(data: dict) -> InstanceSettings:
        java = data.get("java") if isinstance(data.get("java"), dict) else {}
        window = data.get("window") if isinstance(data.get("window"), dict) else {}
        launch = data.get("launch") if isinstance(data.get("launch"), dict) else {}

        min_memory = SettingsManager._as_positive_int(java.get("min_memory"), 1024)
        max_memory = SettingsManager._as_positive_int(java.get("max_memory"), 2048)
        min_memory, max_memory = MemoryAllocationPolicy.normalize(min_memory, max_memory)

        return InstanceSettings(
            java_path=str(java.get("path") or ""),
            min_memory=min_memory,
            max_memory=max_memory,
            jvm_arguments=SettingsManager._as_string_list(java.get("arguments")),
            game_arguments=SettingsManager._as_string_list(launch.get("game_arguments")),
            width=SettingsManager._as_positive_int(window.get("width"), 1280),
            height=SettingsManager._as_positive_int(window.get("height"), 720),
            fullscreen=SettingsManager._as_bool(window.get("fullscreen"), False),
            offline_multiplayer_enabled=SettingsManager._as_bool(launch.get("offline_multiplayer_enabled"), False),
            block_launch_on_modrinth_failure=SettingsManager._as_bool(launch.get("block_launch_on_modrinth_failure"), True),
        )

    @staticmethod
    def _settings_to_dict(settings: InstanceSettings) -> dict:
        return {
            "java": {
                "path": str(settings.java_path or ""),
                "min_memory": int(settings.min_memory),
                "max_memory": int(settings.max_memory),
                "arguments": [str(argument) for argument in settings.jvm_arguments],
            },
            "window": {
                "width": int(settings.width),
                "height": int(settings.height),
                "fullscreen": bool(settings.fullscreen),
            },
            "launch": {
                "game_arguments": [str(argument) for argument in settings.game_arguments],
                "offline_multiplayer_enabled": bool(settings.offline_multiplayer_enabled),
                "block_launch_on_modrinth_failure": bool(settings.block_launch_on_modrinth_failure),
            },
        }

    @staticmethod
    def _write(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.tmp")
        payload = json.dumps(data, indent=4, ensure_ascii=False) + "\n"
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as file:
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def _backup_broken_file(path: Path) -> None:
        if not path.exists():
            return
        candidate = path.with_name(f"{path.name}.broken")
        counter = 2
        while candidate.exists():
            candidate = path.with_name(f"{path.name}.broken.{counter}")
            counter += 1
        try:
            path.replace(candidate)
        except OSError:
            return

    @staticmethod
    def _as_positive_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError, OverflowError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _as_string_list(value: Any) -> list[str]:
        if not isinstance(value, (list, tuple)):
            return []
        return [str(item) for item in value]

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default
