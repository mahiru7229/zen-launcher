from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    authorization_code: str | None = None
    returned_state: str | None = None
    error: str | None = None
    error_description: str | None = None

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)

        OAuthCallbackHandler.authorization_code = query.get("code", [None])[0]
        OAuthCallbackHandler.returned_state = query.get("state", [None])[0]
        OAuthCallbackHandler.error = query.get("error", [None])[0]
        OAuthCallbackHandler.error_description = query.get(
            "error_description",
            [None]
        )[0]

        if OAuthCallbackHandler.authorization_code:
            message = """
            <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Zen Launcher</title>
                </head>
                <body>
                    <h2>Microsoft login completed.</h2>
                    <p>You can close this window and return to MCW Launcher.</p>
                </body>
            </html>
            """
            status = 200
        else:
            message = """
            <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Zen Launcher</title>
                </head>
                <body>
                    <h2>Microsoft login failed.</h2>
                    <p>You can close this window and return to MCW Launcher.</p>
                </body>
            </html>
            """
            status = 400

        body = message.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass


class OAuthCallbackServer:

    @staticmethod
    def wait_for_callback(timeout: float = 180.0) -> tuple[str, str]:
        OAuthCallbackHandler.authorization_code = None
        OAuthCallbackHandler.returned_state = None
        OAuthCallbackHandler.error = None
        OAuthCallbackHandler.error_description = None

        server = HTTPServer(("localhost", 8400), OAuthCallbackHandler)
        server.timeout = timeout

        try:
            server.handle_request()
        finally:
            server.server_close()

        if OAuthCallbackHandler.error:
            description = (
                OAuthCallbackHandler.error_description
                or OAuthCallbackHandler.error
            )

            raise RuntimeError(
                f"Microsoft authorization failed: {description}"
            )

        if not OAuthCallbackHandler.authorization_code:
            raise TimeoutError(
                "Microsoft authorization callback was not received."
            )

        if not OAuthCallbackHandler.returned_state:
            raise RuntimeError(
                "Microsoft authorization callback did not contain state."
            )

        return (
            OAuthCallbackHandler.authorization_code,
            OAuthCallbackHandler.returned_state
        )