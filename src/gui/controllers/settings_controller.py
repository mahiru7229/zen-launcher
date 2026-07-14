from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal

from src.core.instance.instance_manager import InstanceManager
from src.core.instance.settings_manager import SettingsManager
from src.gui.controllers.base_controller import BaseController


class InstanceSettingsController(BaseController):
    settings_loaded = Signal(str, object)
    settings_saved = Signal(str, object)

    def load(self, instance_name: str) -> None:
        instance_name = instance_name.strip()
        if not instance_name:
            self.settings_loaded.emit("", None)
            return
        try:
            instance = InstanceManager.load(instance_name)
            settings = SettingsManager.load(instance)
        except Exception as error:
            self._emit_error("Instance settings", error)
            return
        self.settings_loaded.emit(instance_name, settings)

    def save(self, instance_name: str, data: dict) -> None:
        instance_name = instance_name.strip()
        if not instance_name:
            self._emit_error("Instance settings", "Select an instance first.")
            return
        try:
            min_memory = int(data["min_memory"])
            max_memory = int(data["max_memory"])
            width = int(data["width"])
            height = int(data["height"])
            java_path = str(data["java_path"]).strip()
            if min_memory <= 0 or max_memory < min_memory:
                raise ValueError("Maximum memory must be greater than or equal to minimum memory.")
            if width <= 0 or height <= 0:
                raise ValueError("Window dimensions must be positive.")
            if java_path and not Path(java_path).exists():
                raise FileNotFoundError(f"Java path does not exist: {java_path}")

            instance = InstanceManager.load(instance_name)
            settings = SettingsManager.load(instance)
            settings.java_path = java_path
            settings.min_memory = min_memory
            settings.max_memory = max_memory
            settings.width = width
            settings.height = height
            settings.fullscreen = bool(data["fullscreen"])
            settings.offline_multiplayer_enabled = bool(data["offline_multiplayer_enabled"])
            settings.jvm_arguments = list(data["jvm_arguments"])
            settings.game_arguments = list(data["game_arguments"])
            SettingsManager.save(instance, settings)
        except Exception as error:
            self._emit_error("Save instance settings", error)
            return

        self.settings_saved.emit(instance_name, settings)
        self.settings_loaded.emit(instance_name, settings)
        self.status_changed.emit(f"Saved settings for '{instance_name}'")
        self.log_created.emit(f"Instance settings saved: {instance_name}")
