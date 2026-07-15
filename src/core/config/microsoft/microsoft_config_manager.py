from __future__ import annotations

import json

from src.core.config.microsoft.microsoft_config import MicrosoftConfig
from src.core.fs.paths import Paths


class MicrosoftConfigManager:
    @staticmethod
    def load() -> MicrosoftConfig:
        path = Paths.microsoft_config_root()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            payload = {}
        client_id = str(payload.get("client_id") or "").strip() if isinstance(payload, dict) else ""
        return MicrosoftConfig(client_id=client_id)
