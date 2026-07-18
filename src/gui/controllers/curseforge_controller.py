from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_mod_installer import CurseForgeModInstaller
from src.core.curseforge.curseforge_pack_installer import CurseForgePackInstaller
from src.core.instance.instance_manager import InstanceManager
from src.core.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class CurseForgeController(BaseController):
    search_results_changed = Signal(str, object)
    files_changed = Signal(str, int, list)
    mod_installed = Signal(object)
    modpack_installed = Signal(object)
    progress_received = Signal(object)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, project_type: str, query: str, sort: str, index: int, game_version: str = "") -> None:
        task_id = f"curseforge.search.{project_type}"
        self._task_runner.run(
            task_id,
            lambda: (
                project_type,
                CurseForgeClient.search_projects(
                    project_type=project_type,
                    query=query,
                    game_version=game_version,
                    index=index,
                    page_size=25,
                    sort=sort,
                ),
            ),
            f"Searching CurseForge {project_type}s...",
            blocking=False,
        )

    def load_files(self, project_type: str, project_id: int, game_version: str, allowed_release_types: tuple[str, ...]) -> None:
        task_id = f"curseforge.files.{project_type}.{project_id}"
        self._task_runner.run(
            task_id,
            lambda: (
                project_type,
                int(project_id),
                CurseForgeClient.list_files(
                    project_id,
                    game_version=game_version,
                    release_types=allowed_release_types,
                    page_size=50,
                ),
            ),
            "Loading compatible CurseForge files...",
            blocking=False,
        )

    def install_mod(self, instance_name: str, project_id: int, file_id: int, allowed_release_types: tuple[str, ...]) -> None:
        reporter = ProgressReporter(self.progress_received.emit)

        def task() -> object:
            instance = InstanceManager.load(instance_name)
            return CurseForgeModInstaller.install(
                instance,
                project_id,
                file_id,
                install_dependencies=True,
                allowed_release_types=allowed_release_types,
                reporter=reporter,
            )

        self._task_runner.run("curseforge.install.mod", task, f"Installing CurseForge mod into '{instance_name}'...")

    def install_modpack(self, project_id: int, file_id: int, instance_name: str, install_optional_files: bool, allowed_release_types: tuple[str, ...]) -> None:
        reporter = ProgressReporter(self.progress_received.emit)
        self._task_runner.run(
            "curseforge.install.modpack",
            lambda: CurseForgePackInstaller.install(
                project_id,
                file_id,
                instance_name,
                install_optional_files=install_optional_files,
                allowed_release_types=allowed_release_types,
                reporter=reporter,
            ),
            f"Installing CurseForge modpack '{instance_name}'...",
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith("curseforge.search."):
            if not isinstance(result, tuple) or len(result) != 2:
                self._emit_error("CurseForge", "CurseForge search returned an invalid result.")
                return
            project_type, search_result = result
            self.search_results_changed.emit(str(project_type), search_result)
            return
        if task_id.startswith("curseforge.files."):
            if not isinstance(result, tuple) or len(result) != 3:
                self._emit_error("CurseForge", "CurseForge files returned an invalid result.")
                return
            project_type, project_id, files = result
            self.files_changed.emit(str(project_type), int(project_id), list(files))
            return
        if task_id == "curseforge.install.mod":
            self.status_changed.emit("CurseForge mod installed")
            self.log_created.emit("Installed CurseForge mod and required dependencies")
            self.mod_installed.emit(result)
            return
        if task_id == "curseforge.install.modpack":
            self.status_changed.emit("CurseForge modpack installed")
            self.log_created.emit("Created Forge instance from CurseForge modpack")
            self.modpack_installed.emit(result)

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("curseforge."):
            return
        if task_id == "curseforge.install.mod":
            title = "Install CurseForge mod"
        elif task_id == "curseforge.install.modpack":
            title = "Install CurseForge modpack"
        else:
            title = "CurseForge"
        self._emit_error(title, error)
