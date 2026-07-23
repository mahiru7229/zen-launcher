from __future__ import annotations

from PySide6.QtCore import Signal, Slot

from src.core.modloader.fabric.fabric_meta_client import FabricMetaClient
from src.core.modloader.forge.forge_metadata_client import ForgeMetadataClient
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class ModLoaderController(BaseController):
    fabric_versions_changed = Signal(str, list)
    forge_versions_changed = Signal(str, list)

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def load_fabric_versions(self, game_version: str) -> None:
        game_version = game_version.strip()
        if not game_version:
            return

        task_id = f"fabric.versions:{game_version}"
        if self._task_runner.is_task_active(task_id):
            return
        self._task_runner.run(task_id, lambda: (game_version, FabricMetaClient.list_loader_versions(game_version)), f"Loading Fabric versions for Minecraft {game_version}...", blocking=False)

    def load_forge_versions(self, game_version: str) -> None:
        game_version = game_version.strip()
        if not game_version:
            return
        task_id = f"forge.versions:{game_version}"
        if self._task_runner.is_task_active(task_id):
            return
        self._task_runner.run(task_id, lambda: (game_version, ForgeMetadataClient.list_versions(game_version)), f"Loading Forge versions for Minecraft {game_version}...", blocking=False)

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id.startswith("fabric.versions:"):
            game_version, versions = result
            self.fabric_versions_changed.emit(game_version, list(versions))
            self.log_created.emit(f"Fabric versions loaded for Minecraft {game_version}: {len(versions)}")
            return
        if task_id.startswith("forge.versions:"):
            game_version, versions = result
            self.forge_versions_changed.emit(game_version, list(versions))
            self.log_created.emit(f"Forge versions loaded for Minecraft {game_version}: {len(versions)}")

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id.startswith("fabric.versions:"):
            game_version = task_id.partition(":")[2]
            self.fabric_versions_changed.emit(game_version, [])
            self._emit_error("Fabric Loader", error)
        elif task_id.startswith("forge.versions:"):
            game_version = task_id.partition(":")[2]
            self.forge_versions_changed.emit(game_version, [])
            self._emit_error("Minecraft Forge", error)
