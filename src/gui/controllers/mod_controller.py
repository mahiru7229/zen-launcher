from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from src.core.mod.mod_manager import ModManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner
from src.models.instance.instance import Instance


class ModController(BaseController):
    mods_changed = Signal(list)
    instance_changed = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._instance: Instance | None = None
        self._scan_pending = False
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._scan_pending = False
        self.instance_changed.emit(instance)
        if instance is None:
            self.mods_changed.emit([])
            return
        self.refresh()

    def refresh(self) -> None:
        instance = self._require_instance()
        if instance is None:
            return

        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name != ModLoaderManager.FABRIC:
            self.mods_changed.emit([])
            return

        if self._task_runner.is_task_active("mods.scan"):
            self._scan_pending = True
            return

        instance_id = instance.instance_id
        started = self._task_runner.run("mods.scan", lambda: (instance_id, ModManager.list_mods(instance)), f"Scanning mods for '{instance.name}'...", blocking=False)
        if not started:
            self._scan_pending = True

    def add(self, paths: list[Path], replace: bool = False) -> None:
        instance = self._require_instance()
        if instance is None or not paths:
            return
        self._task_runner.run("mods.add", lambda: ModManager.add_mods(instance, paths, replace), f"Adding {len(paths)} mod file(s)...")

    def remove(self, paths: list[Path]) -> None:
        instance = self._require_instance()
        if instance is None or not paths:
            return
        self._task_runner.run("mods.remove", lambda: ModManager.remove_mods(instance, paths), f"Removing {len(paths)} mod file(s)...")

    def set_enabled(self, paths: list[Path], enabled: bool) -> None:
        instance = self._require_instance()
        if instance is None or not paths:
            return
        action = "Enabling" if enabled else "Disabling"
        self._task_runner.run("mods.toggle", lambda: ModManager.set_enabled(instance, paths, enabled), f"{action} {len(paths)} mod file(s)...")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "mods.scan":
            instance_id, mods = result
            if self._instance is not None and self._instance.instance_id == instance_id:
                self.mods_changed.emit(list(mods))
            self._run_pending_scan()
            return
        if task_id in {"mods.add", "mods.remove", "mods.toggle"}:
            self.status_changed.emit("Mod folder updated")
            self.log_created.emit(f"Completed task: {task_id}")
            self.refresh()

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id.startswith("mods."):
            self._emit_error("Manage mods", error)
        if task_id == "mods.scan":
            self._run_pending_scan()

    def _run_pending_scan(self) -> None:
        if not self._scan_pending:
            return
        self._scan_pending = False
        self.refresh()

    def _require_instance(self) -> Instance | None:
        if self._instance is None:
            self._emit_error("Manage mods", "Select an instance first.")
            return None
        return self._instance
