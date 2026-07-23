from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import json
import os

from src.config import CURSEFORGE_GATEWAY_URL
from src.core.fs.paths import Paths


class CurseForgeConfigManager:
    ENV_GATEWAY_URL = "MCW_CURSEFORGE_GATEWAY_URL"
    ENV_CLIENT_TOKEN = "MCW_CURSEFORGE_CLIENT_TOKEN"

    @staticmethod
    def path() -> Path:
        return Paths.CONFIG_ROOT / "curseforge.json"

    @staticmethod
    def gateway_url() -> str:
        environment = str(os.environ.get(CurseForgeConfigManager.ENV_GATEWAY_URL) or "").strip()
        if environment:
            return CurseForgeConfigManager._normalize_url(environment)
        data = CurseForgeConfigManager._load()
        configured = str(data.get("gateway_url") or "").strip()
        return CurseForgeConfigManager._normalize_url(configured or CURSEFORGE_GATEWAY_URL)

    @staticmethod
    def client_token() -> str:
        environment = str(os.environ.get(CurseForgeConfigManager.ENV_CLIENT_TOKEN) or "").strip()
        if environment:
            return environment
        data = CurseForgeConfigManager._load()
        return str(data.get("client_token") or "").strip()

    @staticmethod
    def is_configured() -> bool:
        try:
            value = CurseForgeConfigManager.gateway_url()
        except ValueError:
            return False
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.netloc)

    @staticmethod
    def save_local(gateway_url: str, client_token: str = "") -> Path:
        value = CurseForgeConfigManager._normalize_url(gateway_url)
        path = CurseForgeConfigManager.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "gateway_url": value,
                    "client_token": str(client_token).strip(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    @staticmethod
    def _load() -> dict:
        try:
            data = json.loads(CurseForgeConfigManager.path().read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _normalize_url(value: str) -> str:
        normalized = str(value).strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("CurseForge gateway URL must be a valid HTTPS URL.")
        return normalized
