from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal, Slot

from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class VersionController(BaseController):
    versions_changed = Signal(list)

    TASK_ID = "versions.load"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def refresh(self) -> None:
        self._task_runner.run(self.TASK_ID, self._load_versions, "Loading Minecraft version manifest...", blocking=False)

    @staticmethod
    def _load_versions() -> list[Any]:
        versions = VersionManifestManager.get()
        if not versions:
            raise RuntimeError("Minecraft version manifest is unavailable.")
        return versions

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != self.TASK_ID:
            return
        versions = list(result)
        self.versions_changed.emit(versions)
        if not self._task_runner.is_busy:
            self.status_changed.emit(f"Loaded {len(versions)} Minecraft versions")
        self.log_created.emit(f"Version manifest loaded: {len(versions)} entries")

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == self.TASK_ID:
            self._emit_error("Version manifest", error)
