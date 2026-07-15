from __future__ import annotations

VERSION = "v0.5.0 Beta 9"
VERSION_ID = "0.5.0-beta.9"
VERSION_TAG = f"v{VERSION_ID}"
UPDATE_CHANNEL = "beta"
GITHUB_REPOSITORY = "mahiru7229/mcw-launcher"
DEVELOPER_NAME = "mahiru7229"
LAUNCHER_SLUG = "mcw-launcher"
LAUNCHER_NAME = f"MCW LAUNCHER {VERSION}"
MODRINTH_USER_AGENT = f"{DEVELOPER_NAME}/{LAUNCHER_SLUG}/{VERSION_ID} (https://github.com/{GITHUB_REPOSITORY})"

# Microsoft authentication remains gated until the launcher application is approved.
MICROSOFT_AUTH_ENABLED = False
MICROSOFT_AUTH_STATUS = "pending_mojang_approval"
