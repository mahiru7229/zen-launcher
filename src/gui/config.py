from __future__ import annotations

import sys
from pathlib import Path

VERSION = "v0.5.0 Beta 3"
VERSION_ID = "0.5.0-beta.3"
UPDATE_CHANNEL = "beta"
GITHUB_REPOSITORY = "mahiru7229/mcw-launcher"
LAUNCHER_NAME = f"MCW LAUNCHER {VERSION}"
DEVELOPER_NAME = "mahiru7229"

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
MINIMUM_WIDTH = 1180
MINIMUM_HEIGHT = 700
SIDEBAR_WIDTH = 220
RIGHT_PANEL_WIDTH = 400

NAVIGATION_ITEMS = (
    ("home", "Home"),
    ("accounts", "Accounts"),
    ("instances", "Instances"),
    ("instance_settings", "Instance Settings"),
    ("launcher_settings", "Launcher Settings"),
    ("logs", "Logs"),
    ("about", "About"),
)


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    return application_root().joinpath("assets", *parts)


MAIN_LOGO_PATH = asset_path("images", "logo", "main_launcher_logo.png")
