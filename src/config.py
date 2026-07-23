from __future__ import annotations

VERSION = "v0.7.0 Beta 1"
VERSION_ID = "0.7.0-beta.1"
VERSION_TAG = f"v{VERSION_ID}"
UPDATE_CHANNEL = "beta"
GITHUB_REPOSITORY = "mahiru7229/mcw-launcher"
DEVELOPER_NAME = "mahiru7229"
LAUNCHER_SLUG = "mcw-launcher"
LAUNCHER_NAME = f"MCW LAUNCHER {VERSION}"
MODRINTH_USER_AGENT = f"{DEVELOPER_NAME}/{LAUNCHER_SLUG}/{VERSION_ID} (https://github.com/{GITHUB_REPOSITORY})"
CURSEFORGE_USER_AGENT = MODRINTH_USER_AGENT

# CurseForge requests are routed through the MCW gateway. The CurseForge API
# key remains on the server and is never bundled into the launcher.
CURSEFORGE_GATEWAY_URL = "https://mcw-curseforge-gateway.vercel.app/api/curseforge"
CURSEFORGE_CACHE_MAX_BYTES = 10 * 1024 * 1024
CURSEFORGE_MANUAL_REFRESH_COOLDOWN_SECONDS = 0

# Microsoft authentication is available in public builds.
MICROSOFT_AUTH_ENABLED = True
MICROSOFT_AUTH_STATUS = "available"
MICROSOFT_CLIENT_ID = "cd379605-ee06-466a-a588-7a1f7c23b48a"

# Security: Minecraft access tokens are short-lived and are kept in memory only.
PERSIST_MICROSOFT_ACCESS_TOKEN = False
