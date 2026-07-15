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


def test_launch_button_text_never_changes(app):
    widget = LaunchControlWidget()
    event = ProgressEvent(stage=ProgressStage.DOWNLOADING_ASSETS, message="Downloading assets...", current=1, total=2)

    assert widget.launch_button.text() == "Launch"

    widget.set_selected_instance(SimpleNamespace(name="Test Instance"))
    widget.set_busy(True)
    widget.set_progress_event(event)
    widget.set_result({"minecraftVersion": "1.21", "javaPath": "javaw.exe"})
    widget.set_failed("Failed")
    widget.set_busy(False)
    widget.reset_progress()

    assert widget.launch_button.text() == "Launch"


def test_exit_result_shows_instance_and_keeps_launch_button_text(app):
    widget = LaunchControlWidget()
    result = SimpleNamespace(instance_name="Runtime Test", crashed=True, exit_code=1, duration_seconds=75)

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

