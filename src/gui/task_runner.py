from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot


class TaskWorker(QObject):
    succeeded = Signal(str, object)
    failed = Signal(str, object)

    def __init__(self, task_id: str, task: Callable[[], Any]) -> None:
        super().__init__()
        self._task_id = task_id
        self._task = task

    @Slot()
    def run(self) -> None:
        try:
            self.succeeded.emit(self._task_id, self._task())
        except Exception as error:
            self.failed.emit(self._task_id, error)


@dataclass(slots=True)
class TaskContext:
    task_id: str
    thread: QThread
    worker: TaskWorker
    blocking: bool


class TaskRunner(QObject):
    task_started = Signal(str, str, bool)
    task_succeeded = Signal(str, object)
    task_failed = Signal(str, object)
    busy_changed = Signal(bool)
    task_rejected = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._contexts: dict[str, TaskContext] = {}
        self._blocking_tasks = 0

    @property
    def is_busy(self) -> bool:
        return self._blocking_tasks > 0

    @property
    def has_active_tasks(self) -> bool:
        return bool(self._contexts)

    def is_task_active(self, task_id: str) -> bool:
        return task_id in self._contexts

    def run(self, task_id: str, task: Callable[[], Any], message: str, blocking: bool = True) -> bool:
        if self.is_task_active(task_id):
            self.task_rejected.emit(f"Task '{task_id}' is already running.")
            return False
        if blocking and self.is_busy:
            self.task_rejected.emit("Another task is still running.")
            return False

        thread = QThread(self)
        worker = TaskWorker(task_id, task)
        worker.moveToThread(thread)
        self._contexts[task_id] = TaskContext(task_id=task_id, thread=thread, worker=worker, blocking=blocking)

        if blocking:
            self._blocking_tasks += 1
            if self._blocking_tasks == 1:
                self.busy_changed.emit(True)

        thread.started.connect(worker.run)
        worker.succeeded.connect(self._finish_success, Qt.ConnectionType.QueuedConnection)
        worker.failed.connect(self._finish_failure, Qt.ConnectionType.QueuedConnection)
        worker.succeeded.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self.task_started.emit(task_id, message, blocking)
        thread.start()
        return True

    def close(self) -> None:
        if self.has_active_tasks:
            raise RuntimeError("Cannot close TaskRunner while a task is active.")

    @Slot(str, object)
    def _finish_success(self, task_id: str, result: Any) -> None:
        context = self._contexts.pop(task_id, None)
        if context is None:
            return
        self.task_succeeded.emit(task_id, result)
        self._finish_context(context)

    @Slot(str, object)
    def _finish_failure(self, task_id: str, error: Exception) -> None:
        context = self._contexts.pop(task_id, None)
        if context is None:
            return
        self.task_failed.emit(task_id, error)
        self._finish_context(context)

    def _finish_context(self, context: TaskContext) -> None:
        if context.blocking:
            self._blocking_tasks = max(0, self._blocking_tasks - 1)
            if self._blocking_tasks == 0:
                self.busy_changed.emit(False)
        context.thread.quit()
