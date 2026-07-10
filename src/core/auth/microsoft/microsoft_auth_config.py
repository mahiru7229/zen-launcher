from src.core.config.microsoft.microsoft_config_manager import MicrosoftConfigManager
import os


class MicrosoftAuthConfig:
    config = MicrosoftConfigManager.load()
    CLIENT_ID = config.client_id
    TENANT = "consumers"

    AUTHORIZE_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/authorize"
    TOKEN_URL = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"

    REDIRECT_URI = "http://localhost:8400"

    SCOPES = [
        "XboxLive.signin",
        "offline_access"
    ]