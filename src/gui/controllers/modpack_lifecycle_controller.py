from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from src.core.instance.instance_manager import InstanceManager
from src.core.language.language_manager import tr
from src.core.modrinth.modrinth_pack_registry import ModrinthPackRegistry
from src.core.modrinth.modrinth_pack_update_manager import ModrinthPackUpdateManager
from src.core.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ModpackLifecycleController(BaseController):
    state_changed = Signal(object)
    update_checked = Signal(object)
    update_finished = Signal(object)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def scan(self, instance_name: str) -> None:
        name = str(instance_name).strip()
        if not name:
            return
        self._task_runner.run("modpack.scan", lambda: ModrinthPackRegistry.scan(InstanceManager.load(name)), tr("Scanning Modrinth pack files for '{name}'...", name=name), blocking=False)

    def check_update(self, instance_name: str, allowed_version_types: tuple[str, ...], force_refresh: bool = True) -> None:
        name = str(instance_name).strip()
        if not name:
            return
        self._task_runner.run("modpack.update.check", lambda: ModrinthPackUpdateManager.check(InstanceManager.load(name), allowed_version_types, force_refresh=force_refresh), tr("Checking modpack updates for '{name}'...", name=name), blocking=False)

    def update(self, instance_name: str, allowed_version_types: tuple[str, ...]) -> None:
        name = str(instance_name).strip()
        if not name:
            return
        reporter = ProgressReporter(self.progress_received.emit)
        self._task_runner.run("modpack.update.apply", lambda: ModrinthPackUpdateManager.update(InstanceManager.load(name), allowed_version_types=allowed_version_types, reporter=reporter), tr("Updating Modrinth modpack for '{name}'...", name=name))

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "modpack.scan":
            self.state_changed.emit(result)
            return
        if task_id == "modpack.update.check":
            self.update_checked.emit(result)
            return
        if task_id == "modpack.update.apply":
            self.update_finished.emit(result)
            self.status_changed.emit(tr("Modrinth modpack updated"))
            self.log_created.emit(tr("Modrinth modpack updated to {version}", version=getattr(result, "target_version", "")))

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id.startswith("modpack."):
            self._emit_error(tr("Modrinth modpack"), error)
