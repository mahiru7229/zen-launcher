from __future__ import annotations

from time import time
from uuid import uuid4

from src.core.auth.microsoft.microsoft_auth_gate import MicrosoftAuthenticationGate
from src.core.auth.microsoft.microsoft_auth_config import MicrosoftAuthConfig
from src.core.auth.microsoft.microsoft_oauth import MicrosoftOAuth
from src.core.auth.microsoft.minecraft_profile_client import MinecraftProfileClient
from src.core.auth.microsoft.minecraft_services_auth import MinecraftServicesAuthentication
from src.core.auth.microsoft.xbox_live_auth import XboxLiveAuthentication
from src.core.auth.microsoft.xsts_auth import XSTSAuthentication
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


class MicrosoftAccountAuthenticator:
    @staticmethod
    def authenticate() -> Account:
        MicrosoftAuthenticationGate.require_enabled()
        if not str(MicrosoftAuthConfig.CLIENT_ID).strip():
            raise RuntimeError("Microsoft authentication is enabled but no client_id is configured.")
        oauth_token = MicrosoftOAuth.authenticate()
        xbox_token = XboxLiveAuthentication.authenticate(oauth_token.access_token)
        xsts_token = XSTSAuthentication.authenticate(xbox_token)
        minecraft_token = MinecraftServicesAuthentication.authenticate(xsts_token)
        MinecraftProfileClient.verify_entitlement(minecraft_token.access_token)
        profile = MinecraftProfileClient.get_profile(minecraft_token.access_token)
        return Account(account_id=str(uuid4()), account_type=AccountSource.MICROSOFT, username=profile.name, uuid=profile.profile_id, access_token=minecraft_token.access_token, refresh_token=oauth_token.refresh_token, token_expires_at=int(time()) + int(minecraft_token.expires_in))

    @staticmethod
    def refresh(account: Account) -> Account:
        MicrosoftAuthenticationGate.require_enabled()
        if not str(MicrosoftAuthConfig.CLIENT_ID).strip():
            raise RuntimeError("Microsoft authentication is enabled but no client_id is configured.")
        if account.account_type is not AccountSource.MICROSOFT or not account.refresh_token:
            raise RuntimeError("This account does not contain a Microsoft refresh token.")
        oauth_token = MicrosoftOAuth.refresh(account.refresh_token)
        xbox_token = XboxLiveAuthentication.authenticate(oauth_token.access_token)
        xsts_token = XSTSAuthentication.authenticate(xbox_token)
        minecraft_token = MinecraftServicesAuthentication.authenticate(xsts_token)
        MinecraftProfileClient.verify_entitlement(minecraft_token.access_token)
        profile = MinecraftProfileClient.get_profile(minecraft_token.access_token)
        account.username = profile.name
        account.uuid = profile.profile_id
        account.access_token = minecraft_token.access_token
        account.refresh_token = oauth_token.refresh_token
        account.token_expires_at = int(time()) + int(minecraft_token.expires_in)
        return account
