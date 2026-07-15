from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from src.core.backup.instance_backup_manager import InstanceBackupManager
from src.core.instance.instance_manager import InstanceManager
from src.core.language.language_manager import tr
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class BackupController(BaseController):
    backup_created = Signal(object)
    restore_finished = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def create(self, instance_name: str, scope: str) -> None:
        name = str(instance_name).strip()
        if not name:
            return
        self._task_runner.run("backup.create", lambda: InstanceBackupManager.create(InstanceManager.load(name), scope=scope), tr("Creating {scope} backup for '{name}'...", scope=scope, name=name))

    def restore(self, instance_name: str, backup_path: Path) -> None:
        name = str(instance_name).strip()
        path = Path(backup_path)
        if not name:
            return
        self._task_runner.run("backup.restore", lambda: InstanceBackupManager.restore(InstanceManager.load(name), path), tr("Restoring backup for '{name}'...", name=name))

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "backup.create":
            self.backup_created.emit(result)
            path = getattr(getattr(result, "backup", None), "path", "")
            self.status_changed.emit(tr("Instance backup created"))
            self.log_created.emit(tr("Instance backup created: {path}", path=path))
        elif task_id == "backup.restore":
            self.restore_finished.emit(result)
            self.status_changed.emit(tr("Instance backup restored"))
            self.log_created.emit(tr("Instance backup restored: {path}", path=getattr(result, "backup_path", "")))

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id.startswith("backup."):
            self._emit_error(tr("Instance backup"), error)
