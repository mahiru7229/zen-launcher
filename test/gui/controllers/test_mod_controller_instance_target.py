from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.controllers.mod_controller import ModController


class _Signal:
    def connect(self, _slot: object) -> None:
        return None


class _TaskRunner:
    def __init__(self) -> None:
        self.task_succeeded = _Signal()
        self.task_failed = _Signal()


def test_set_instance_can_defer_initial_scan(monkeypatch) -> None:
    controller = ModController(_TaskRunner())
    refresh_calls: list[bool] = []
    monkeypatch.setattr(controller, "refresh", lambda: refresh_calls.append(True))
    instance = SimpleNamespace(instance_id="id", name="Created", mod_loader=("fabric", "0.16.14"))

    controller.set_instance(instance, refresh=False)

    assert controller.current_instance is instance
    assert refresh_calls == []
