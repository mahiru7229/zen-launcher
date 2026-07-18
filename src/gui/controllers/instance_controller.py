from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Slot

from src.core.instance.instance_manager import InstanceManager
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.minecraft.library_manager import DownloadLibraryManager
from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.progress.progress_reporter import ProgressReporter
from src.core.runtime.instance_repair_manager import InstanceRepairManager
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class InstanceController(BaseController):
    instances_changed = Signal(list, str)
    running_instances_changed = Signal(list)
    selected_instance_changed = Signal(object)
    export_finished = Signal(object)
    repair_progress = Signal(object)
    loader_progress = Signal(object)
    package_progress = Signal(object)
    repair_finished = Signal(object)

    REPAIR_TASK_ID = "instance.repair.full"
    INSTANCE_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1F]{1,80}$')

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._selected_name = ""
        self._running_signature: tuple[tuple[object, ...], ...] | None = None
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def refresh(self, selected_name: str = "") -> None:
        try:
            instances = sorted(InstanceManager.list_instances(), key=lambda item: item.name.casefold())
        except Exception as error:
            self._emit_error("Instances", error)
            return

        names = [instance.name for instance in instances]
        preferred = selected_name or self._selected_name
        if preferred not in names:
            preferred = names[0] if names else ""
        self._selected_name = preferred
        self.instances_changed.emit(instances, preferred)
        self.select(preferred)
        self.log_created.emit(f"Instances refreshed: {len(instances)} found")

    def refresh_running(self, force: bool = False) -> None:
        running_instances = InstanceRunLock.list_active()
        signature = tuple((item.instance_id, item.name, item.state, item.launcher_pid, item.minecraft_pid) for item in running_instances)

        if not force and signature == self._running_signature:
            return

        self._running_signature = signature
        self.running_instances_changed.emit(running_instances)

    def select(self, name: str) -> None:
        self._selected_name = name.strip()
        if not self._selected_name:
            self.selected_instance_changed.emit(None)
            return
        try:
            instance = InstanceManager.load(self._selected_name)
        except Exception as error:
            self._emit_error("Load instance", error)
            return
        self.selected_instance_changed.emit(instance)

    def create(self, name: str, version_id: str, loader_name: str = "vanilla", loader_version: str = ModLoaderManager.AUTO) -> None:
        name = self._validated_name(name)
        version_id = version_id.strip()
        loader_name, loader_version = ModLoaderManager.normalize((loader_name, loader_version))
        if name is None or not version_id:
            if not version_id:
                self._emit_error("Create instance", "Select a Minecraft version first.")
            return

        reporter = ProgressReporter(self._on_loader_progress)

        def task() -> Any:
            version = VersionManager.load(version_id)
            resolved_loader = ModLoaderManager.resolve(version.id, loader_name, loader_version)
            ModLoaderManager.prepare(version, *resolved_loader, reporter=reporter)
            return InstanceManager.create(name=name, version=version, mod_loader=resolved_loader)

        self._task_runner.run("instance.create", task, f"Creating instance '{name}'...")

    def change_loader(self, name: str, loader_name: str, loader_version: str) -> None:
        name = name.strip()
        loader_name, loader_version = ModLoaderManager.normalize((loader_name, loader_version))
        if not name:
            return
        if loader_name == ModLoaderManager.FABRIC and not loader_version:
            self._emit_error("Change mod loader", "Select a Fabric Loader version first.")
            return

        reporter = ProgressReporter(self._on_loader_progress)

        def task() -> Any:
            instance = InstanceManager.load(name)
            if InstanceRunLock.is_active(instance):
                raise RuntimeError("Close Minecraft before changing this instance's mod loader.")
            version = VersionManager.load(instance.version_id)
            resolved_loader = ModLoaderManager.resolve(version.id, loader_name, loader_version)
            ModLoaderManager.prepare(version, *resolved_loader, reporter=reporter)
            return InstanceManager.set_mod_loader(name, resolved_loader)

        self._task_runner.run("instance.loader", task, f"Applying {loader_name.title()} to '{name}'...")

    def repair_loader(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        reporter = ProgressReporter(self._on_loader_progress)

        def task() -> Any:
            instance = InstanceManager.load(name)
            if InstanceRunLock.is_active(instance):
                raise RuntimeError("Close Minecraft before repairing this instance's mod loader.")
            version = ModLoaderManager.repair(instance, reporter=reporter)
            DownloadLibraryManager.load(version, reporter=reporter)
            return instance

        self._task_runner.run("instance.loader.repair", task, f"Repairing mod loader for '{name}'...")


    def repair_instance(self, name: str) -> None:
        name = name.strip()
        if not name:
            return

        def task() -> Any:
            instance = InstanceManager.load(name)
            return InstanceRepairManager.repair(instance, on_progress=self._on_repair_progress)

        self._task_runner.run(self.REPAIR_TASK_ID, task, f"Repairing '{name}'...")

    def _on_repair_progress(self, event: object) -> None:
        self.repair_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "repair")
        message = str(getattr(event, "message", "Repairing instance..."))
        self.log_created.emit(f"[{stage}] {message}")

    def _on_loader_progress(self, event: object) -> None:
        self.loader_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "mod_loader")
        message = str(getattr(event, "message", "Preparing mod loader..."))
        self.log_created.emit(f"[{stage}] {message}")

    def rename(self, source_name: str, target_name: str) -> None:
        source_name = source_name.strip()
        target_name = self._validated_name(target_name)
        if not source_name or target_name is None:
            return

        def task() -> dict[str, str]:
            InstanceManager.rename(source_name, target_name)
            return {"source": source_name, "target": target_name}

        self._task_runner.run("instance.rename", task, f"Renaming '{source_name}'...")

    def clone(self, source_name: str, target_name: str, include_saves: bool) -> None:
        source_name = source_name.strip()
        target_name = self._validated_name(target_name)
        if not source_name or target_name is None:
            return

        def task() -> Any:
            return InstanceManager.clone(source_name=source_name, new_name=target_name, include_saves=include_saves)

        self._task_runner.run("instance.clone", task, f"Cloning '{source_name}'...")

    def delete(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.delete", lambda: {"name": name, "deleted": InstanceManager.delete_instance(name)}, f"Deleting '{name}'...")

    def import_package(self, package_path: Path) -> None:
        self._task_runner.run("instance.import", lambda: InstanceManager.import_instance(package_path, self._on_package_progress), f"Importing '{package_path.name}'...")

    def export_package(self, name: str, output_path: Path, include_saves: bool) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.export", lambda: InstanceManager.export(name, output_path, include_saves, self._on_package_progress), f"Exporting '{name}'...")

    def _on_package_progress(self, event: object) -> None:
        self.package_progress.emit(event)
        stage = getattr(getattr(event, "stage", None), "value", "package")
        message = str(getattr(event, "message", "Processing package..."))
        self.log_created.emit(f"[{stage}] {message}")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        selected_name = self._selected_name
        if task_id == "instance.create":
            selected_name = result.name
            self.status_changed.emit(f"Created '{selected_name}'")
        elif task_id == "instance.rename":
            selected_name = result["target"]
            self.status_changed.emit(f"Renamed '{result['source']}' to '{selected_name}'")
        elif task_id == "instance.clone":
            selected_name = result.name
            self.status_changed.emit(f"Cloned instance as '{selected_name}'")
        elif task_id == "instance.delete":
            if not result["deleted"]:
                self._emit_error("Delete instance", "Instance was not found.")
                return
            selected_name = ""
            self.status_changed.emit(f"Deleted '{result['name']}'")
        elif task_id == "instance.import":
            selected_name = result.name
            self.status_changed.emit(f"Imported '{selected_name}'")
        elif task_id == "instance.loader":
            selected_name = result.name
            loader_name, loader_version = ModLoaderManager.normalize(result.mod_loader)
            loader_text = loader_name if loader_name == "vanilla" else f"{loader_name} {loader_version}"
            self.status_changed.emit(f"Applied {loader_text} to '{selected_name}'")
        elif task_id == "instance.loader.repair":
            selected_name = result.name
            self.status_changed.emit(f"Repaired Fabric for '{selected_name}'")
        elif task_id == self.REPAIR_TASK_ID:
            selected_name = result.instance_name
            self.repair_finished.emit(result)
            self.status_changed.emit(f"Repaired instance '{selected_name}'")
        elif task_id == "instance.export":
            self.export_finished.emit(result)
            self.status_changed.emit("Instance export completed")
            self.log_created.emit(f"Instance exported to: {result}")
            return
        else:
            return

        self.log_created.emit(self.status_changed_message(task_id, result))
        self.refresh(selected_name)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id.startswith("instance."):
            self._emit_error("Instance task", error)

    def _validated_name(self, name: str) -> str | None:
        name = name.strip()
        if not name:
            self._emit_error("Instance name", "Enter an instance name.")
            return None
        if name in {".", ".."} or not self.INSTANCE_NAME_PATTERN.fullmatch(name) or name.endswith((" ", ".")):
            self._emit_error("Instance name", "The instance name is not valid on Windows.")
            return None
        return name

    @staticmethod
    def status_changed_message(task_id: str, result: object) -> str:
        if task_id == "instance.rename":
            return f"Instance renamed: {result['source']} -> {result['target']}"
        if task_id == "instance.delete":
            return f"Instance deleted: {result['name']}"
        if hasattr(result, "name"):
            return f"Instance task completed: {result.name}"
        return f"Instance task completed: {task_id}"
