import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.controllers.modrinth_controller import ModrinthController
from src.gui.task_runner import TaskRunner


def test_controller_ignores_unrelated_task_result(gui_app):
    controller = ModrinthController(TaskRunner())
    emitted = []
    controller.search_results_changed.connect(lambda *args: emitted.append(args))

    controller._on_task_succeeded("versions.load", "x" * 901)

    assert emitted == []


def test_controller_emits_loader_with_search_results(gui_app):
    controller = ModrinthController(TaskRunner())
    emitted = []
    controller.search_results_changed.connect(lambda *args: emitted.append(args))
    result = object()

    controller._on_task_succeeded("modrinth.search.mod.forge", ("mod", "forge", result))

    assert emitted == [("mod", "forge", result)]


def test_controller_passes_forge_filter_to_client(gui_app, monkeypatch):
    task_runner = TaskRunner()
    controller = ModrinthController(task_runner)
    calls = []
    monkeypatch.setattr(task_runner, "run", lambda task_id, task, message, blocking=False: calls.append((task_id, task(), message, blocking)))

    from src.core.modrinth.modrinth_client import ModrinthClient
    monkeypatch.setattr(ModrinthClient, "search_projects", lambda **kwargs: kwargs)

    controller.search("mod", "jei", "downloads", 0, game_version="1.20.1", loader="forge")

    assert calls[0][0] == "modrinth.search.mod.forge"
    assert calls[0][1][0:2] == ("mod", "forge")
    assert calls[0][1][2]["loader"] == "forge"


def test_controller_forces_live_search_refresh(gui_app, monkeypatch):
    task_runner = TaskRunner()
    controller = ModrinthController(task_runner)
    calls = []
    monkeypatch.setattr(task_runner, "run", lambda task_id, task, message, blocking=False: calls.append(task()))

    from src.core.modrinth.modrinth_client import ModrinthClient
    monkeypatch.setattr(ModrinthClient, "search_projects", lambda **kwargs: kwargs)

    controller.search("modpack", "", "downloads", 0, loader="fabric")

    assert calls[0][2]["force_refresh"] is True


def test_controller_emits_inline_search_failure(gui_app):
    controller = ModrinthController(TaskRunner())
    emitted = []
    controller.search_failed.connect(lambda *args: emitted.append(args))

    controller._on_task_failed("modrinth.search.modpack.forge", RuntimeError("network unavailable"))

    assert emitted == [("modpack", "forge", "network unavailable")]
