from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_manual_installer import CurseForgeManualInstaller
from src.core.curseforge.curseforge_mod_installer import CurseForgeModInstaller
from src.core.curseforge.curseforge_pack_installer import CurseForgePackInstaller
from src.core.instance.instance_manager import InstanceManager
from src.core.progress.progress_reporter import ProgressReporter
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner
from src.models.curseforge.cache import CurseForgeFileListResult
from src.models.curseforge.manual_download import CurseForgeManualDownload


class CurseForgeController(BaseController):
    search_results_changed = Signal(str, object)
    files_changed = Signal(str, int, list)
    cache_info_changed = Signal(str, object)
    catalog_search_results_changed = Signal(str, object)
    catalog_files_changed = Signal(int, str, list)
    catalog_cache_info_changed = Signal(object)
    catalog_request_failed = Signal(str, str, str)
    mod_installed = Signal(object)
    manual_file_installed = Signal(str, object, str)
    modpack_installed = Signal(object)
    cache_cleared = Signal(object)
    progress_received = Signal(object)

    DIALOG_CONTEXT = "dialog"
    CATALOG_CONTEXT = "catalog"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def search(self, project_type: str, query: str, sort: str, index: int, game_version: str = "", loader: str = "forge", force_refresh: bool = False, manual_refresh: bool = False, context: str = DIALOG_CONTEXT) -> bool:
        normalized_context = self._normalize_context(context)
        normalized_loader = CurseForgeClient.normalize_loader(loader) or "forge"
        task_id = f"curseforge.search.{normalized_context}.{project_type}.{normalized_loader}"
        return self._task_runner.run(
            task_id,
            lambda: (
                normalized_context,
                project_type,
                normalized_loader,
                CurseForgeClient.search_projects(
                    project_type=project_type,
                    query=query,
                    game_version=game_version,
                    loader=normalized_loader,
                    index=index,
                    page_size=25,
                    sort=sort,
                    force_refresh=force_refresh,
                    manual_refresh=manual_refresh,
                ),
            ),
            f"Searching CurseForge {project_type}s...",
            blocking=False,
        )

    def load_files(self, project_type: str, project_id: int, game_version: str, loader: str, allowed_release_types: tuple[str, ...], force_refresh: bool = False, manual_refresh: bool = False, context: str = DIALOG_CONTEXT) -> bool:
        normalized_context = self._normalize_context(context)
        normalized_loader = CurseForgeClient.normalize_loader(loader) or "forge"
        task_id = f"curseforge.files.{normalized_context}.{project_type}.{project_id}.{normalized_loader}"
        return self._task_runner.run(
            task_id,
            lambda: (
                normalized_context,
                project_type,
                int(project_id),
                normalized_loader,
                CurseForgeClient.list_files_result(
                    project_id,
                    game_version=game_version,
                    loader=normalized_loader,
                    release_types=allowed_release_types,
                    page_size=50,
                    force_refresh=force_refresh,
                    manual_refresh=manual_refresh,
                ),
            ),
            "Loading compatible CurseForge files...",
            blocking=False,
        )

    def install_mod(self, instance_name: str, project_id: int, file_id: int, allowed_release_types: tuple[str, ...]) -> bool:
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

        return self._task_runner.run("curseforge.install.mod", task, f"Installing CurseForge mod into '{instance_name}'...")

    def install_manual_file(self, instance_name: str, requirement: CurseForgeManualDownload, source: Path) -> bool:
        task_id = f"curseforge.install.manual.{requirement.project_id}"
        return self._task_runner.run(
            task_id,
            lambda: (
                instance_name,
                requirement,
                CurseForgeManualInstaller.install(InstanceManager.load(instance_name), requirement, source),
            ),
            f"Importing manually downloaded CurseForge file '{requirement.file_name}'...",
        )

    def install_modpack(self, project_id: int, file_id: int, instance_name: str, install_optional_files: bool, allowed_release_types: tuple[str, ...]) -> bool:
        reporter = ProgressReporter(self.progress_received.emit)
        return self._task_runner.run(
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

    def clear_cache(self, context: str = DIALOG_CONTEXT) -> bool:
        normalized_context = self._normalize_context(context)
        return self._task_runner.run(
            f"curseforge.cache.clear.{normalized_context}",
            lambda: (normalized_context, (CurseForgeClient.clear_cache(), CurseForgeClient.cache_status())[1]),
            "Clearing CurseForge cache...",
            blocking=False,
        )

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith("curseforge.search."):
            if not isinstance(result, tuple) or len(result) != 4:
                self._emit_error("CurseForge", "CurseForge search returned an invalid result.")
                return
            context, project_type, loader, search_result = result
            if context == self.CATALOG_CONTEXT:
                self.catalog_search_results_changed.emit(str(loader), search_result)
                self.catalog_cache_info_changed.emit(getattr(search_result, "cache_info", CurseForgeClient.cache_status()))
            else:
                self.search_results_changed.emit(str(project_type), search_result)
                self.cache_info_changed.emit(str(project_type), getattr(search_result, "cache_info", CurseForgeClient.cache_status()))
            return
        if task_id.startswith("curseforge.files."):
            if not isinstance(result, tuple) or len(result) != 5:
                self._emit_error("CurseForge", "CurseForge files returned an invalid result.")
                return
            context, project_type, project_id, loader, file_result = result
            if not isinstance(file_result, CurseForgeFileListResult):
                self._emit_error("CurseForge", "CurseForge files returned an invalid cache result.")
                return
            if context == self.CATALOG_CONTEXT:
                self.catalog_files_changed.emit(int(project_id), str(loader), list(file_result.files))
                self.catalog_cache_info_changed.emit(file_result.cache_info)
            else:
                self.files_changed.emit(str(project_type), int(project_id), list(file_result.files))
                self.cache_info_changed.emit(str(project_type), file_result.cache_info)
            return
        if task_id == "curseforge.install.mod":
            self.status_changed.emit("CurseForge mod installed")
            self.log_created.emit("Installed CurseForge mod and required dependencies")
            self.mod_installed.emit(result)
            return
        if task_id.startswith("curseforge.install.manual."):
            if isinstance(result, tuple) and len(result) == 3:
                instance_name, requirement, installed_name = result
                self.manual_file_installed.emit(str(instance_name), requirement, str(installed_name))
                self.status_changed.emit("CurseForge manual file imported")
                self.log_created.emit(f"Imported manually downloaded CurseForge file: {installed_name}")
            return
        if task_id == "curseforge.install.modpack":
            self.status_changed.emit("CurseForge modpack installed")
            self.log_created.emit("Created Forge instance from CurseForge modpack")
            self.modpack_installed.emit(result)
            return
        if task_id.startswith("curseforge.cache.clear."):
            if not isinstance(result, tuple) or len(result) != 2:
                self._emit_error("CurseForge", "CurseForge cache clear returned an invalid result.")
                return
            context, info = result
            self.cache_cleared.emit(info)
            if context == self.CATALOG_CONTEXT:
                self.catalog_cache_info_changed.emit(info)
            else:
                self.cache_info_changed.emit("mod", info)
                self.cache_info_changed.emit("modpack", info)
            self.status_changed.emit("CurseForge cache cleared")

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if not task_id.startswith("curseforge."):
            return
        if task_id.startswith("curseforge.search.catalog."):
            loader = task_id.rsplit(".", 1)[-1]
            self.catalog_request_failed.emit("search", loader, str(error) or "CurseForge search failed.")
            return
        if task_id.startswith("curseforge.files.catalog."):
            parts = task_id.split(".")
            project_id = parts[-2] if len(parts) >= 2 else "0"
            loader = parts[-1] if parts else ""
            self.catalog_request_failed.emit(f"files:{project_id}", loader, str(error) or "CurseForge files request failed.")
            return
        if task_id.startswith("curseforge.cache.clear.catalog"):
            self.catalog_request_failed.emit("cache", "", str(error) or "Could not clear CurseForge cache.")
            return
        if task_id == "curseforge.install.mod":
            title = "Install CurseForge mod"
        elif task_id.startswith("curseforge.install.manual."):
            title = "Import CurseForge file"
        elif task_id == "curseforge.install.modpack":
            title = "Install CurseForge modpack"
        else:
            title = "CurseForge"
        self._emit_error(title, error)

    @classmethod
    def _normalize_context(cls, context: str) -> str:
        normalized = str(context or cls.DIALOG_CONTEXT).strip().lower()
        return normalized if normalized in {cls.DIALOG_CONTEXT, cls.CATALOG_CONTEXT} else cls.DIALOG_CONTEXT
