from __future__ import annotations

import sys
from pathlib import Path

from src.config import DEVELOPER_NAME, GITHUB_REPOSITORY, LAUNCHER_NAME, UPDATE_CHANNEL, VERSION, VERSION_ID

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
