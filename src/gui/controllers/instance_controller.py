from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Slot

from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.version_manager import VersionManager
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class InstanceController(BaseController):
    instances_changed = Signal(list, str)
    selected_instance_changed = Signal(object)
    export_finished = Signal(object)

    INSTANCE_NAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1F]{1,80}$')

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._selected_name = ""
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

    def create(self, name: str, version_id: str) -> None:
        name = self._validated_name(name)
        version_id = version_id.strip()
        if name is None or not version_id:
            if not version_id:
                self._emit_error("Create instance", "Select a Minecraft version first.")
            return

        def task() -> Any:
            return InstanceManager.create(name=name, version=VersionManager.load(version_id))

        self._task_runner.run("instance.create", task, f"Creating instance '{name}'...")

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
        self._task_runner.run("instance.import", lambda: InstanceManager.import_instance(package_path), f"Importing '{package_path.name}'...")

    def export_package(self, name: str, output_path: Path, include_saves: bool) -> None:
        name = name.strip()
        if not name:
            return
        self._task_runner.run("instance.export", lambda: InstanceManager.export(name, output_path, include_saves), f"Exporting '{name}'...")

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
