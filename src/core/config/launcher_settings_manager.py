from __future__ import annotations

import base64
import copy
import json
import os
import threading
from pathlib import Path
from typing import Any

from src.core.fs.paths import Paths


class LauncherSettingsManager:
    SCHEMA_VERSION = 1
    DEFAULT_SETTINGS = {
        "schema_version": SCHEMA_VERSION,
        "gui": {
            "start_page": "home",
            "show_snapshots": False,
            "remember_window_size": True,
            "language": "en-US",
        },
        "launch": {
            "debug_mode": False,
        },
        "window": {
            "geometry": None,
        },
    }

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else Paths.launcher_settings_path()
        self._lock = threading.RLock()

    def initialize(self) -> Path:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self._write(copy.deepcopy(self.DEFAULT_SETTINGS))
            else:
                data = self._read_or_recover()
                normalized = self._normalize(data)
                if normalized != data:
                    self._write(normalized)
            return self.path

    def load(self) -> dict[str, Any]:
        with self._lock:
            self.initialize()
            return copy.deepcopy(self._normalize(self._read_or_recover()))

    def save(self, settings: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(settings, dict):
            raise TypeError("Launcher settings must be a dictionary.")

        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            current = self._read_or_recover() if self.path.exists() else copy.deepcopy(self.DEFAULT_SETTINGS)
            merged = self._deep_merge(current, settings)
            normalized = self._normalize(merged)
            self._write(normalized)
            return copy.deepcopy(normalized)

    def update_section(self, section: str, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            raise TypeError("Launcher settings section must be a dictionary.")
        return self.save({str(section): values})

    def reset(self) -> dict[str, Any]:
        with self._lock:
            defaults = copy.deepcopy(self.DEFAULT_SETTINGS)
            self._write(defaults)
            return defaults

    def load_window_geometry(self) -> bytes | None:
        encoded = self.load().get("window", {}).get("geometry")
        if not isinstance(encoded, str) or not encoded:
            return None
        try:
            return base64.b64decode(encoded.encode("ascii"), validate=True)
        except (ValueError, UnicodeEncodeError):
            return None

    def save_window_geometry(self, geometry: bytes | bytearray | memoryview) -> None:
        encoded = base64.b64encode(bytes(geometry)).decode("ascii")
        self.update_section("window", {"geometry": encoded})

    def _read_or_recover(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Launcher settings root must be an object.")
            return data
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            self._backup_broken_file()
            defaults = copy.deepcopy(self.DEFAULT_SETTINGS)
            self._write(defaults)
            return defaults

    def _backup_broken_file(self) -> None:
        if not self.path.exists():
            return

        candidate = self.path.with_name(f"{self.path.name}.broken")
        counter = 2
        while candidate.exists():
            candidate = self.path.with_name(f"{self.path.name}.broken.{counter}")
            counter += 1

        try:
            self.path.replace(candidate)
        except OSError:
            try:
                self.path.unlink()
            except OSError:
                pass

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_name(f"{self.path.name}.tmp")
        payload = json.dumps(data, indent=4, ensure_ascii=False) + "\n"

        with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())

        temporary_path.replace(self.path)

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = self._deep_merge(copy.deepcopy(self.DEFAULT_SETTINGS), data)
        normalized["schema_version"] = self.SCHEMA_VERSION

        gui = normalized.setdefault("gui", {})
        gui["start_page"] = str(gui.get("start_page") or "home")
        gui["show_snapshots"] = self._as_bool(gui.get("show_snapshots"), False)
        gui["remember_window_size"] = self._as_bool(gui.get("remember_window_size"), True)
        gui["language"] = str(gui.get("language") or "en-US")

        launch = normalized.setdefault("launch", {})
        launch["debug_mode"] = self._as_bool(launch.get("debug_mode"), False)

        window = normalized.setdefault("window", {})
        geometry = window.get("geometry")
        window["geometry"] = geometry if isinstance(geometry, str) and geometry else None

        return normalized

    @classmethod
    def _deep_merge(cls, base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(base)
        for key, value in overlay.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default
