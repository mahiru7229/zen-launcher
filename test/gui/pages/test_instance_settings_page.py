import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
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


def test_memory_sliders_are_limited_by_physical_ram(gui_app) -> None:
    page = InstanceSettingsPage(total_memory_mb=8192)

    assert page.max_memory.maximum() == 8192
    assert page.memory_limit_mb == 8192
    assert page.min_memory.maximum() == page.max_memory.value()


def test_lowering_maximum_memory_clamps_minimum_memory(gui_app) -> None:
    page = InstanceSettingsPage(total_memory_mb=8192)
    page.max_memory.setValue(6144)
    page.min_memory.setValue(6144)

    page.max_memory.setValue(4096)

    assert page.max_memory.value() == 4096
    assert page.min_memory.maximum() == 4096
    assert page.min_memory.value() == 4096


def test_loaded_memory_above_physical_ram_is_clamped(gui_app) -> None:
    page = InstanceSettingsPage(total_memory_mb=8192)
    settings = make_settings(True)
    settings.min_memory = 12288
    settings.max_memory = 16384

    page.set_settings("Pack", settings)

    assert page.form_data()["min_memory"] == 8192
    assert page.form_data()["max_memory"] == 8192


def test_memory_inputs_accept_exact_values_and_sync_sliders(gui_app) -> None:
    page = InstanceSettingsPage(total_memory_mb=8192)

    page.max_memory_input.setValue(5000)
    page.min_memory_input.setValue(1500)

    assert page.max_memory.value() == 5000
    assert page.min_memory.value() == 1500
    assert page.form_data()["max_memory"] == 5000
    assert page.form_data()["min_memory"] == 1500


def test_memory_input_limits_follow_maximum_and_physical_ram(gui_app) -> None:
    page = InstanceSettingsPage(total_memory_mb=8192)
    page.max_memory_input.setValue(6144)
    page.min_memory_input.setValue(6144)

    page.max_memory_input.setValue(4096)

    assert page.max_memory_input.maximum() == 8192
    assert page.min_memory_input.maximum() == 4096
    assert page.min_memory_input.value() == 4096
    assert page.min_memory.value() == 4096


def test_memory_number_inputs_are_left_aligned(gui_app) -> None:
    page = InstanceSettingsPage(total_memory_mb=8192)

    assert page.min_memory_input.alignment() & Qt.AlignmentFlag.AlignLeft
    assert page.max_memory_input.alignment() & Qt.AlignmentFlag.AlignLeft
