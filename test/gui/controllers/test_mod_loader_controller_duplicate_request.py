from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal

from src.gui.controllers.mod_loader_controller import ModLoaderController


class _Runner(QObject):
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.run_calls: list[str] = []

    def is_task_active(self, _task_id: str) -> bool:
        return True

    def run(self, task_id, *_args, **_kwargs):
        self.run_calls.append(task_id)
        return False


def test_duplicate_fabric_version_request_is_ignored_silently() -> None:
    runner = _Runner()
    controller = ModLoaderController(runner)

    controller.load_fabric_versions("1.21.1")

    assert runner.run_calls == []
