from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from src.core.mod.mod_compatibility_manager import ModCompatibilityManager
from src.core.mod.mod_manager import ModManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.modrinth.modrinth_mod_update_manager import ModrinthModUpdateManager
from src.core.modrinth.modrinth_registry import ModrinthRegistry
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner
from src.models.instance.instance import Instance
from src.models.mod.mod_issue import ModHealthReport
from src.models.modrinth.update import ModrinthModUpdateReport


class ModController(BaseController):
    mods_changed = Signal(list)
    health_changed = Signal(object)
    updates_changed = Signal(object)
    instance_changed = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._instance: Instance | None = None
        self._scan_pending = False
        self._last_allowed_types = ("release",)
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    @property
    def current_instance(self) -> Instance | None:
        return self._instance

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._scan_pending = False
        self.instance_changed.emit(instance)
        self.health_changed.emit(ModHealthReport(issues=(), enabled_mods=0, disabled_mods=0))
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

        def scan() -> tuple[str, list, ModHealthReport]:
            mods = ModManager.list_mods(instance)
            return instance_id, mods, ModCompatibilityManager.scan(instance, mods)

        started = self._task_runner.run("mods.scan", scan, f"Scanning mods for '{instance.name}'...", blocking=False)
        if not started:
            self._scan_pending = True

    def add(self, paths: list[Path], replace: bool = False) -> None:
        instance = self._require_instance()
        if instance is None or not paths:
            return
        def add() -> list:
            added = ModManager.add_mods(instance, paths, replace)
            ModrinthRegistry.remove_by_filenames(instance, [mod.file_name for mod in added])
            return added

        self._task_runner.run("mods.add", add, f"Adding {len(paths)} mod file(s)...")

    def remove(self, paths: list[Path]) -> None:
        instance = self._require_instance()
        if instance is None or not paths:
            return
        def remove() -> None:
            filenames = [path.name[:-len(ModManager.DISABLED_SUFFIX)] if path.name.endswith(ModManager.DISABLED_SUFFIX) else path.name for path in paths]
            ModManager.remove_mods(instance, paths)
            ModrinthRegistry.remove_by_filenames(instance, filenames)

        self._task_runner.run("mods.remove", remove, f"Removing {len(paths)} mod file(s)...")

    def set_enabled(self, paths: list[Path], enabled: bool) -> None:
        instance = self._require_instance()
        if instance is None or not paths:
            return
        action = "Enabling" if enabled else "Disabling"
        self._task_runner.run("mods.toggle", lambda: ModManager.set_enabled(instance, paths, enabled), f"{action} {len(paths)} mod file(s)...")

    def check_updates(self, allowed_version_types: tuple[str, ...], force_refresh: bool = True) -> None:
        instance = self._require_instance()
        if instance is None:
            return
        instance_id = instance.instance_id
        self._last_allowed_types = tuple(allowed_version_types)
        self._task_runner.run("mods.update.check", lambda: (instance_id, ModrinthModUpdateManager.check(instance, allowed_version_types, force_refresh=force_refresh)), "Checking Modrinth mod updates...", blocking=False)

    def update_projects(self, project_ids: list[str], allowed_version_types: tuple[str, ...]) -> None:
        instance = self._require_instance()
        if instance is None or not project_ids:
            return
        instance_id = instance.instance_id
        self._last_allowed_types = tuple(allowed_version_types)
        self._task_runner.run("mods.update.apply", lambda: (instance_id, allowed_version_types, ModrinthModUpdateManager.update(instance, project_ids, allowed_version_types)), f"Updating {len(project_ids)} Modrinth mod(s)...")

    def update_all(self, allowed_version_types: tuple[str, ...]) -> None:
        instance = self._require_instance()
        if instance is None:
            return
        instance_id = instance.instance_id
        self._last_allowed_types = tuple(allowed_version_types)
        self._task_runner.run("mods.update.apply", lambda: (instance_id, allowed_version_types, ModrinthModUpdateManager.update_all(instance, allowed_version_types)), "Updating all unlocked Modrinth mods...")

    def set_locked(self, project_ids: list[str], locked: bool) -> None:
        instance = self._require_instance()
        if instance is None or not project_ids:
            return
        instance_id = instance.instance_id
        self._task_runner.run("mods.lock", lambda: (instance_id, ModrinthModUpdateManager.set_locked(instance, project_ids, locked)), "Updating mod version locks...", blocking=False)

    def analyze(self) -> None:
        instance = self._require_instance()
        if instance is None:
            return
        instance_id = instance.instance_id
        self._task_runner.run("mods.health", lambda: (instance_id, ModCompatibilityManager.scan(instance)), "Analyzing Fabric mod compatibility...", blocking=False)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == "mods.scan":
            instance_id, mods, health = result
            if self._matches_instance(instance_id):
                self.mods_changed.emit(list(mods))
                self.health_changed.emit(health)
            self._run_pending_scan()
            return
        if task_id == "mods.update.check":
            instance_id, report = result
            if self._matches_instance(instance_id):
                self.updates_changed.emit(report)
            return
        if task_id == "mods.update.apply":
            instance_id, allowed_types, update_result = result
            if self._matches_instance(instance_id):
                count = len(update_result.updated_projects)
                self.status_changed.emit(f"Updated {count} Modrinth mod(s)")
                self.log_created.emit(f"Updated Modrinth mods: {', '.join(update_result.updated_projects) or 'none'}")
                for warning in update_result.warnings:
                    self.log_created.emit(f"Mod update warning: {warning}")
                if update_result.skipped_locked:
                    self.log_created.emit(f"Skipped locked mods: {', '.join(update_result.skipped_locked)}")
                self.refresh()
                self.check_updates(tuple(allowed_types))
            return
        if task_id == "mods.lock":
            instance_id, changed = result
            if self._matches_instance(instance_id):
                self.status_changed.emit(f"Updated {len(changed)} mod version lock(s)")
                self.refresh()
                self.check_updates(self._last_allowed_types)
            return
        if task_id == "mods.health":
            instance_id, report = result
            if self._matches_instance(instance_id):
                self.health_changed.emit(report)
            return
        if task_id in {"mods.add", "mods.remove", "mods.toggle"}:
            if task_id in {"mods.add", "mods.remove"}:
                self.updates_changed.emit(ModrinthModUpdateReport(entries=()))
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

    def _matches_instance(self, instance_id: str) -> bool:
        return self._instance is not None and self._instance.instance_id == instance_id

    def _require_instance(self) -> Instance | None:
        if self._instance is None:
            self._emit_error("Manage mods", "Select an instance first.")
            return None
        return self._instance
