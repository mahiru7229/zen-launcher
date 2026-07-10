from urllib.parse import urlencode
import httpx
from src.models.auth.microsoft.microsoft_oauth_token import MicrosoftOAuthToken
import secrets
import webbrowser
from src.core.auth.microsoft.oauth_callback_server import OAuthCallbackServer
from src.core.auth.microsoft.microsoft_auth_config import MicrosoftAuthConfig
from src.core.auth.microsoft.pkce import PKCE
from src.models.auth.microsoft.oauth_session import OAuthSession


class MicrosoftOAuth:


    @staticmethod
    def authenticate() -> MicrosoftOAuthToken:
        authorization_code, code_verifier = (
            MicrosoftOAuth.request_authorization_code()
        )

        return MicrosoftOAuth.exchange_code(
            authorization_code,
            code_verifier
        )

    @staticmethod
    def exchange_code(authorization_code: str, code_verifier: str) -> MicrosoftOAuthToken:
        data = {
            "client_id": MicrosoftAuthConfig.CLIENT_ID,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": MicrosoftAuthConfig.REDIRECT_URI,
            "code_verifier": code_verifier,
            "scope": " ".join(MicrosoftAuthConfig.SCOPES),
        }

        try:
            response = httpx.post(
                MicrosoftAuthConfig.TOKEN_URL,
                data=data,
                timeout=30.0
            )

            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            error_data = e.response.json()

            error = error_data.get("error", "unknown_error")
            description = error_data.get(
                "error_description",
                "Microsoft token request failed."
            )

            raise RuntimeError(
                f"Microsoft OAuth token error: {error}: {description}"
            ) from e

        except httpx.HTTPError as e:
            raise RuntimeError(
                "Could not connect to Microsoft OAuth."
            ) from e

        return MicrosoftOAuthToken.from_dict(response.json())

    @staticmethod
    def request_authorization_code() -> tuple[str, str]:
        session = MicrosoftOAuth.create_session()

        opened = MicrosoftOAuth.open_browser(session)

        if not opened:
            raise RuntimeError(
                "Could not open the default browser."
            )

        authorization_code, returned_state = (
            OAuthCallbackServer.wait_for_callback()
        )

        if not secrets.compare_digest(
            returned_state,
            session.state
        ):
            raise RuntimeError(
                "Microsoft authorization state does not match."
            )

        return authorization_code, session.code_verifier

    @staticmethod
    def create_session() -> OAuthSession:
        code_verifier = PKCE.generate_verifier()
        code_challenge = PKCE.create_challenge(code_verifier)
        state = secrets.token_urlsafe(32)

        parameters = {
            "client_id": MicrosoftAuthConfig.CLIENT_ID,
            "response_type": "code",
            "redirect_uri": MicrosoftAuthConfig.REDIRECT_URI,
            "response_mode": "query",
            "scope": " ".join(MicrosoftAuthConfig.SCOPES),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
        }

        authorization_url = (
            MicrosoftAuthConfig.AUTHORIZE_URL
            + "?"
            + urlencode(parameters)
        )

        return OAuthSession(
            authorization_url=authorization_url,
            code_verifier=code_verifier,
            state=state
        )

    @staticmethod
    def open_browser(session: OAuthSession) -> bool:
        return webbrowser.open(session.authorization_url)