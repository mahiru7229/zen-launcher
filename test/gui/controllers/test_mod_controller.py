import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.controllers.mod_controller import ModController
from src.gui.task_runner import TaskRunner
from src.models.instance.instance import Instance
from src.models.modrinth.update import ModrinthModUpdateEntry, ModrinthModUpdateReport


def test_update_check_report_does_not_publish_main_launcher_status(gui_app, tmp_path):
    runner = TaskRunner()
    controller = ModController(runner)
    instance = Instance(instance_id="id", name="Fabric", version_id="1.20.1", instance_dir=tmp_path, mod_loader=("fabric", "0.19.3"))
    controller._instance = instance
    statuses: list[str] = []
    reports: list[ModrinthModUpdateReport] = []
    controller.status_changed.connect(statuses.append)
    controller.updates_changed.connect(reports.append)
    report = ModrinthModUpdateReport(entries=(ModrinthModUpdateEntry(project_id="project", title="Example", file_name="example.jar", current_version_id="old", current_version_number="1.0", latest_version_id="new", latest_version_number="2.0", latest_version_type="release"),))

    controller._on_task_succeeded("mods.update.check", (instance.instance_id, report))

    assert reports == [report]
    assert statuses == []
    gui_app.processEvents()
