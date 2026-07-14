from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Signal, Slot

from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.language.language_manager import tr
from src.core.update.update_manager import UpdateManager
from src.gui.config import GITHUB_REPOSITORY, UPDATE_CHANNEL, VERSION_ID
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner
from src.models.update.update_info import UpdateInfo


class UpdateController(BaseController):
    update_available = Signal(object, bool)
    no_update_available = Signal(bool)
    update_prepared = Signal(object)
    update_check_failed = Signal(object, bool)

    AUTO_CHECK_TASK_ID = "update.check.auto"
    MANUAL_CHECK_TASK_ID = "update.check.manual"
    PREPARE_TASK_ID = "update.prepare"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._manager = UpdateManager(repository=GITHUB_REPOSITORY, current_version=VERSION_ID, channel=UPDATE_CHANNEL)
        self._settings = LauncherSettingsManager()
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def check(self, manual: bool = False) -> None:
        task_id = self.MANUAL_CHECK_TASK_ID if manual else self.AUTO_CHECK_TASK_ID
        self._task_runner.run(task_id, lambda: self._manager.check_for_update(force_refresh=manual), tr("update.status.checking"), blocking=False)

    def prepare(self, info: UpdateInfo) -> None:
        self._task_runner.run(self.PREPARE_TASK_ID, lambda: self._manager.prepare_update(info), tr("update.status.downloading"), blocking=True)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id not in {self.AUTO_CHECK_TASK_ID, self.MANUAL_CHECK_TASK_ID, self.PREPARE_TASK_ID}:
            return

        if task_id == self.PREPARE_TASK_ID:
            self.status_changed.emit(tr("update.status.ready"))
            self.log_created.emit(tr("update.log.prepared"))
            self.update_prepared.emit(result)
            return

        manual = task_id == self.MANUAL_CHECK_TASK_ID
        self._settings.update_section("updates", {"last_checked_at": datetime.now(timezone.utc).isoformat()})
        if result is None:
            self.status_changed.emit(tr("update.status.latest"))
            self.no_update_available.emit(manual)
            return
        if not isinstance(result, UpdateInfo):
            self.update_check_failed.emit(RuntimeError("Update check returned an invalid result."), manual)
            return

        self.status_changed.emit(tr("update.status.available", version=result.version))
        self.log_created.emit(tr("update.log.available", version=result.version))
        self.update_available.emit(result, manual)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.PREPARE_TASK_ID:
            self._emit_error(tr("update.error.title"), error)
            return
        if task_id not in {self.AUTO_CHECK_TASK_ID, self.MANUAL_CHECK_TASK_ID}:
            return

        manual = task_id == self.MANUAL_CHECK_TASK_ID
        self.log_created.emit(tr("update.log.check_failed", error=error))
        self.update_check_failed.emit(error, manual)
