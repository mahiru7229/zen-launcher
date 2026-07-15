import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.pages.instance_settings_page import InstanceSettingsPage


def make_settings(block_launch_on_modrinth_failure: bool) -> SimpleNamespace:
    return SimpleNamespace(
        java_path="",
        min_memory=1024,
        max_memory=2048,
        width=1280,
        height=720,
        fullscreen=False,
        offline_multiplayer_enabled=False,
        block_launch_on_modrinth_failure=block_launch_on_modrinth_failure,
        jvm_arguments=[],
        game_arguments=[],
    )


def test_modrinth_failure_option_is_enabled_by_default(gui_app) -> None:
    page = InstanceSettingsPage()

    assert page.block_modrinth_failure.isChecked() is True


def test_modrinth_failure_option_loads_and_serializes_per_instance(gui_app) -> None:
    page = InstanceSettingsPage()

    page.set_settings("Pack", make_settings(False))

    assert page.block_modrinth_failure.isChecked() is False
    assert page.form_data()["block_launch_on_modrinth_failure"] is False
