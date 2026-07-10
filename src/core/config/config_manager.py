from src.core.fs.paths import Paths
import json




class ConfigManager:
    @staticmethod
    def microsoft_client_id() -> str:
        return json.loads(Paths.microsoft_config_root().read_text(encoding="utf-8")).get("client_id")