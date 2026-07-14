from __future__ import annotations

from PySide6.QtCore import QByteArray, Signal

from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.language.language_manager import tr
from src.gui.controllers.base_controller import BaseController


class GuiSettingsController(BaseController):
    settings_changed = Signal(dict)

    DEFAULTS = {
        "start_page": "home",
        "show_snapshots": False,
        "debug_mode": False,
        "remember_window_size": True,
        "language": "en-US",
        "auto_check_updates": True,
        "update_channel": "beta",
    }

    def __init__(self) -> None:
        super().__init__()
        self._settings = LauncherSettingsManager()
        self._current = dict(self.DEFAULTS)

    @property
    def current(self) -> dict:
        return dict(self._current)

    def raw_settings(self) -> dict:
        return self._settings.load()

    def load(self) -> dict:
        data = self._settings.load()
        gui = data.get("gui", {})
        launch = data.get("launch", {})
        updates = data.get("updates", {})
        self._current = {
            "start_page": str(gui.get("start_page", self.DEFAULTS["start_page"])),
            "show_snapshots": bool(gui.get("show_snapshots", self.DEFAULTS["show_snapshots"])),
            "debug_mode": bool(launch.get("debug_mode", self.DEFAULTS["debug_mode"])),
            "remember_window_size": bool(gui.get("remember_window_size", self.DEFAULTS["remember_window_size"])),
            "language": str(gui.get("language", self.DEFAULTS["language"])),
            "auto_check_updates": bool(updates.get("auto_check", self.DEFAULTS["auto_check_updates"])),
            "update_channel": str(updates.get("channel", self.DEFAULTS["update_channel"])),
        }
        self.settings_changed.emit(dict(self._current))
        return dict(self._current)

    def save(self, data: dict) -> None:
        self._current = {
            "start_page": str(data.get("start_page", self.DEFAULTS["start_page"])),
            "show_snapshots": bool(data.get("show_snapshots", self.DEFAULTS["show_snapshots"])),
            "debug_mode": bool(data.get("debug_mode", self.DEFAULTS["debug_mode"])),
            "remember_window_size": bool(data.get("remember_window_size", self.DEFAULTS["remember_window_size"])),
            "language": str(data.get("language", self.DEFAULTS["language"])),
            "auto_check_updates": bool(data.get("auto_check_updates", self.DEFAULTS["auto_check_updates"])),
            "update_channel": str(data.get("update_channel", self.DEFAULTS["update_channel"])),
        }
        self._settings.save({
            "gui": {
                "start_page": self._current["start_page"],
                "show_snapshots": self._current["show_snapshots"],
                "remember_window_size": self._current["remember_window_size"],
                "language": self._current["language"],
            },
            "launch": {
                "debug_mode": self._current["debug_mode"],
            },
            "updates": {
                "auto_check": self._current["auto_check_updates"],
                "channel": self._current["update_channel"],
            },
        })
        self.settings_changed.emit(dict(self._current))
        self.status_changed.emit(tr("Launcher settings saved"))
        self.log_created.emit(tr("GUI preferences saved"))


    def set_auto_check_updates(self, enabled: bool) -> None:
        self._current["auto_check_updates"] = bool(enabled)
        self._settings.update_section("updates", {"auto_check": bool(enabled)})
        self.settings_changed.emit(dict(self._current))

    def reset(self) -> None:
        self._settings.reset()
        self.load()
        self.status_changed.emit(tr("Launcher settings saved"))
        self.log_created.emit(tr("GUI preferences saved"))

    def saved_geometry(self) -> QByteArray | None:
        geometry = self._settings.load_window_geometry()
        return QByteArray(geometry) if geometry is not None else None

    def save_geometry(self, geometry: QByteArray) -> None:
        self._settings.save_window_geometry(bytes(geometry))
