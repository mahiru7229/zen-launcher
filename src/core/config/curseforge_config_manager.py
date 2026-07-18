from __future__ import annotations

from pathlib import Path
import json
import os

from src.core.fs.paths import Paths


class CurseForgeConfigManager:
    ENV_KEY = "MCW_CURSEFORGE_API_KEY"

    @staticmethod
    def path() -> Path:
        return Paths.CONFIG_ROOT / "curseforge.json"

    @staticmethod
    def api_key() -> str:
        environment = str(os.environ.get(CurseForgeConfigManager.ENV_KEY) or "").strip()
        if environment:
            return environment
        try:
            data = json.loads(CurseForgeConfigManager.path().read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return ""
        if not isinstance(data, dict):
            return ""
        return str(data.get("api_key") or "").strip()

    @staticmethod
    def is_configured() -> bool:
        return bool(CurseForgeConfigManager.api_key())

    @staticmethod
    def save_local(api_key: str) -> Path:
        value = str(api_key).strip()
        path = CurseForgeConfigManager.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps({"api_key": value}, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
        return path
