from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from src.core.java.java_diagnostics_manager import JavaDiagnosticsManager
from src.core.language.language_manager import tr
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class JavaController(BaseController):
    installations_changed = Signal(list)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def scan(self) -> None:
        self._task_runner.run("java.scan", JavaDiagnosticsManager.scan, tr("Scanning Java installations..."), blocking=False)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != "java.scan":
            return
        installations = list(result) if isinstance(result, (list, tuple)) else []
        self.installations_changed.emit(installations)
        self.log_created.emit(tr("Java scan completed: {count} installation(s)", count=len(installations)))

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == "java.scan":
            self._emit_error(tr("Java scan"), error)
