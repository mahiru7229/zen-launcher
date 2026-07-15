from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from src.core.instance.instance_manager import InstanceManager
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_mod_installer import ModrinthModInstaller
from src.core.modrinth.modrinth_pack_installer import ModrinthPackInstaller
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ModrinthController(BaseController):
    search_results_changed = Signal(str, object)
    versions_changed = Signal(str, str, list)
    mod_installed = Signal(object)
    modpack_installed = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, project_type: str, query: str, index: str, offset: int, game_version: str = "") -> None:
        task_id = f"modrinth.search.{project_type}"
        self._task_runner.run(task_id, lambda: (project_type, ModrinthClient.search_projects(project_type=project_type, query=query, game_version=game_version, loader="fabric", index=index, offset=offset, limit=25)), f"Searching Modrinth {project_type}s...", blocking=False)

    def load_versions(self, project_type: str, project_id: str, game_version: str = "") -> None:
        task_id = f"modrinth.versions.{project_type}.{project_id}"
        self._task_runner.run(task_id, lambda: (project_type, project_id, ModrinthClient.list_project_versions(project_id, loader="fabric", game_version=game_version, version_types=("release", "beta", "alpha"))), "Loading compatible Modrinth versions...", blocking=False)

    def install_mod(self, instance_name: str, version_id: str, allowed_version_types: tuple[str, ...] = ("release",)) -> None:
        def task() -> object:
            instance = InstanceManager.load(instance_name)
            return ModrinthModInstaller.install(instance, version_id, install_dependencies=True, allowed_version_types=allowed_version_types)

        self._task_runner.run("modrinth.install.mod", task, f"Installing Modrinth mod into '{instance_name}'...")

    def install_modpack(self, project_id: str, version_id: str, instance_name: str, install_optional_files: bool, allowed_version_types: tuple[str, ...] = ("release",)) -> None:
        self._task_runner.run("modrinth.install.modpack", lambda: ModrinthPackInstaller.install(project_id, version_id, instance_name, install_optional_files, allowed_version_types), f"Installing Modrinth modpack '{instance_name}'...")

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith("modrinth.search."):
            if not isinstance(result, tuple) or len(result) != 2:
                self._emit_error("Modrinth", "Modrinth search returned an invalid result.")
                return
            project_type, search_result = result
            self.search_results_changed.emit(str(project_type), search_result)
            return
        if task_id.startswith("modrinth.versions."):
            if not isinstance(result, tuple) or len(result) != 3:
                self._emit_error("Modrinth", "Modrinth versions returned an invalid result.")
                return
            project_type, project_id, versions = result
            self.versions_changed.emit(str(project_type), str(project_id), list(versions))
            return
        if task_id == "modrinth.install.mod":
            self.status_changed.emit("Modrinth mod installed")
            self.log_created.emit("Installed Modrinth mod and required dependencies")
            self.mod_installed.emit(result)
            return
        if task_id == "modrinth.install.modpack":
            self.status_changed.emit("Modrinth modpack installed")
            self.log_created.emit("Created instance from Modrinth modpack")
            self.modpack_installed.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("modrinth."):
            return
        if task_id == "modrinth.install.mod":
            title = "Install Modrinth mod"
        elif task_id == "modrinth.install.modpack":
            title = "Install Modrinth modpack"
        else:
            title = "Modrinth"
        self._emit_error(title, error)
