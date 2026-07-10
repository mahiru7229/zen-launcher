from src.core.config.microsoft.microsoft_config import MicrosoftConfig
from src.core.fs.paths import Paths
import json


class MicrosoftConfigManager:

    @staticmethod
    def load() -> MicrosoftConfig:
        path = Paths.microsoft_config_root()
        client_id = json.loads(path.read_text(encoding="utf-8")).get("client_id")
        return MicrosoftConfig(client_id=client_id)