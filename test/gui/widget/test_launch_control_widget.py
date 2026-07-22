import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_launch_button_switches_to_cancel_during_launch_and_back(app):
    widget = LaunchControlWidget()

    assert widget.launch_button.text() == "Launch"
    assert widget.launch_button.property("themeRole") == "launch"

    widget.set_busy(True)
    assert widget.launch_button.isEnabled() is False

    widget.set_launch_active(True)
    assert widget.launch_button.text() == "Cancel"
    assert widget.launch_button.property("themeRole") == "cancel"
    assert widget.launch_button.isEnabled() is True

    widget.set_pause_pending()
    assert widget.launch_button.text() == "Cancel"
    assert widget.launch_button.isEnabled() is False
    assert widget.stage_label.text() == "PAUSING"

    widget.set_launch_active(False)
    widget.set_busy(False)
    assert widget.launch_button.text() == "Launch"
    assert widget.launch_button.property("themeRole") == "launch"
    assert widget.launch_button.isEnabled() is True


def test_paused_state_keeps_progress_and_invites_resume(app):
    widget = LaunchControlWidget()
    event = ProgressEvent(stage=ProgressStage.DOWNLOADING_ASSETS, message="Downloading assets...", current=1, total=2)

    widget.set_launch_active(True)
    widget.set_progress_event(event)
    widget.set_paused()

    assert widget.stage_label.text() == "PAUSED"
    assert "Press Launch" in widget.detail_label.text()
    assert widget.launch_button.text() == "Launch"
    assert widget.stage_label.property("state") == "warning"


def test_exit_result_shows_instance_and_restores_launch_button(app):
    widget = LaunchControlWidget()
    result = SimpleNamespace(instance_name="Runtime Test", crashed=True, exit_code=1, duration_seconds=75)

    widget.set_launch_active(True)
    widget.set_launch_active(False)
    widget.set_exit_result(result)

    assert "Runtime Test" in widget.status_label.text()
    assert "1" in widget.detail_label.text()
    assert widget.stage_label.text() == "CRASHED"
    assert widget.launch_button.text() == "Launch"


def test_non_blocking_modrinth_warning_is_shown_without_failed_state(app):
    widget = LaunchControlWidget()

    widget.set_result({
        "minecraftVersion": "1.21",
        "javaPath": "javaw.exe",
        "warnings": ("mods/example.jar must be installed manually",),
    })

    assert "warnings" in widget.status_label.text().lower()
    assert "mods/example.jar" in widget.detail_label.text()
    assert widget.stage_label.text() == "WARNING"
    assert widget.stage_label.property("state") == "warning"
    assert widget.launch_button.text() == "Launch"


def test_failed_state_keeps_technical_error_out_of_progress_area(app):
    widget = LaunchControlWidget()
    technical_error = "Forge pre-launch check failed:\n" + "\n".join(f"- broken mod {index}" for index in range(80))

    widget.set_failed(technical_error)

    assert widget.status_label.text() == "Launch failed"
    assert widget.detail_label.text() == "Open Logs to see the full error details."
    assert "broken mod" not in widget.detail_label.text()
    assert widget.stage_label.text() == "FAILED"
