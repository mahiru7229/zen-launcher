from __future__ import annotations

from PySide6.QtCore import QByteArray, QSettings, Signal

from src.gui.controllers.base_controller import BaseController


class GuiSettingsController(BaseController):
    settings_changed = Signal(dict)

    DEFAULTS = {
        "start_page": "home",
        "show_snapshots": False,
        "debug_mode": False,
        "remember_window_size": True,
    }

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("mahiru7229", "MCW Launcher")
        self._current = dict(self.DEFAULTS)

    @property
    def current(self) -> dict:
        return dict(self._current)

    def load(self) -> dict:
        self._current = {
            "start_page": self._settings.value("gui/start_page", self.DEFAULTS["start_page"], type=str),
            "show_snapshots": self._settings.value("gui/show_snapshots", self.DEFAULTS["show_snapshots"], type=bool),
            "debug_mode": self._settings.value("launch/debug_mode", self.DEFAULTS["debug_mode"], type=bool),
            "remember_window_size": self._settings.value("gui/remember_window_size", self.DEFAULTS["remember_window_size"], type=bool),
        }
        self.settings_changed.emit(dict(self._current))
        return dict(self._current)

    def save(self, data: dict) -> None:
        self._current = {
            "start_page": str(data.get("start_page", "home")),
            "show_snapshots": bool(data.get("show_snapshots", False)),
            "debug_mode": bool(data.get("debug_mode", False)),
            "remember_window_size": bool(data.get("remember_window_size", True)),
        }
        self._settings.setValue("gui/start_page", self._current["start_page"])
        self._settings.setValue("gui/show_snapshots", self._current["show_snapshots"])
        self._settings.setValue("launch/debug_mode", self._current["debug_mode"])
        self._settings.setValue("gui/remember_window_size", self._current["remember_window_size"])
        self._settings.sync()
        self.settings_changed.emit(dict(self._current))
        self.status_changed.emit("Launcher settings saved")
        self.log_created.emit("GUI preferences saved")

    def reset(self) -> None:
        self.save(dict(self.DEFAULTS))

    def saved_geometry(self) -> QByteArray | None:
        value = self._settings.value("window/geometry")
        return value if isinstance(value, QByteArray) else None

    def save_geometry(self, geometry: QByteArray) -> None:
        self._settings.setValue("window/geometry", geometry)
