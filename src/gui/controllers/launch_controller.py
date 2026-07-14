from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal, Slot

from src.core.auth.offline_auth import OfflineAuthentication
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.gui.controllers.base_controller import BaseController
from src.gui.presenters.launch_error_presenter import LaunchErrorPresenter
from src.gui.task_runner import TaskRunner
from src.models.progress.progress_event import ProgressEvent


class LaunchController(BaseController):
    progress_received = Signal(object)
    launch_finished = Signal(object)

    TASK_ID = "minecraft.launch"

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()

        self._task_runner = task_runner
        self._selected_instance = None
        self._selected_account = None
        self._debug_mode = False

        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def set_instance(self, instance: object | None) -> None:
        self._selected_instance = instance

    def set_account(self, account: object | None) -> None:
        self._selected_account = account

    def set_debug_mode(self, enabled: bool) -> None:
        self._debug_mode = enabled

    def launch(self) -> None:
        if self._selected_instance is None:
            self._emit_error("Launch Minecraft", "Select an instance first.")
            return

        if self._selected_account is None:
            self._emit_error("Launch Minecraft", "Create or select an account first.")
            return

        instance_name = self._selected_instance.name
        account = self._selected_account
        debug_mode = self._debug_mode

        def task() -> dict[str, Any]:
            instance = InstanceManager.load(instance_name)
            authentication = OfflineAuthentication.authenticate(account)

            return MinecraftExecutor.run(
                instance=instance,
                authentication=authentication,
                account=account,
                debug_mode=debug_mode,
                on_progress=self._on_progress,
            )

        self._task_runner.run(self.TASK_ID, task, f"Launching '{instance_name}'...")

    def _on_progress(self, event: ProgressEvent) -> None:
        self.progress_received.emit(event)
        self.log_created.emit(self._format_progress(event))

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != self.TASK_ID:
            return

        self.launch_finished.emit(result)

        version = result.get("minecraftVersion", "unknown")
        self.status_changed.emit(f"Minecraft {version} launched")
        self.log_created.emit(f"Minecraft process created successfully: {version}")

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id != self.TASK_ID:
            return

        view = LaunchErrorPresenter.present(error)

        self.status_changed.emit(view.status)
        self.log_created.emit(f"{type(error).__name__}: {error}")
        self.error_created.emit(view.title, view.message)

    @staticmethod
    def _format_progress(event: ProgressEvent) -> str:
        stage = event.stage.value

        if event.is_determinate:
            return f"[{stage}] {event.message} {event.current}/{event.total} ({event.percentage or 0:.1f}%)"

        return f"[{stage}] {event.message}"
