from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal, Slot

from src.core.auth.account_authentication import AccountAuthentication
from src.core.instance.instance_manager import InstanceManager
from src.core.language.language_manager import tr
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.gui.controllers.base_controller import BaseController
from src.gui.presenters.launch_error_presenter import LaunchErrorPresenter
from src.gui.task_runner import TaskRunner
from src.models.progress.progress_event import ProgressEvent


class LaunchController(BaseController):
    progress_received = Signal(object)
    launch_finished = Signal(object)
    game_exited = Signal(object)

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
            self._emit_error(tr("Launch Minecraft"), tr("Select an instance first."))
            return

        if self._selected_account is None:
            self._emit_error(tr("Launch Minecraft"), tr("Create or select an account first."))
            return

        instance_name = self._selected_instance.name
        account = self._selected_account
        debug_mode = self._debug_mode

        def task() -> dict[str, Any]:
            instance = InstanceManager.load(instance_name)
            authentication = AccountAuthentication.authenticate(account)

            return MinecraftExecutor.run(
                instance=instance,
                authentication=authentication,
                account=account,
                debug_mode=debug_mode,
                on_progress=self._on_progress,
                on_exit=self._on_game_exit,
            )

        self._task_runner.run(self.TASK_ID, task, tr("Launching '{name}'...", name=instance_name))

    def _on_progress(self, event: ProgressEvent) -> None:
        self.progress_received.emit(event)
        self.log_created.emit(self._format_progress(event))


    def _on_game_exit(self, result: object) -> None:
        self.game_exited.emit(result)
        instance_name = str(getattr(result, "instance_name", "Minecraft"))
        exit_code = int(getattr(result, "exit_code", -1))
        crashed = bool(getattr(result, "crashed", exit_code != 0))
        if crashed:
            self.status_changed.emit(tr("Minecraft crashed: {name}", name=instance_name))
            self.log_created.emit(tr("Minecraft exited with code {code}: {name}", code=exit_code, name=instance_name))
        else:
            self.status_changed.emit(tr("Minecraft closed normally: {name}", name=instance_name))
            self.log_created.emit(tr("Minecraft exited normally: {name}", name=instance_name))

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id != self.TASK_ID:
            return

        self.launch_finished.emit(result)

        version = result.get("minecraftVersion", "unknown")
        warnings = tuple(result.get("warnings", ()) or ())
        if warnings:
            self.status_changed.emit(tr("Minecraft {version} launched with warnings", version=version))
            self.log_created.emit(tr("Minecraft process created with {count} warning(s): {version}", count=len(warnings), version=version))
            for warning in warnings:
                self.log_created.emit(f"Modrinth warning: {warning}")
            return

        self.status_changed.emit(tr("Minecraft {version} launched", version=version))
        self.log_created.emit(tr("Minecraft process created successfully: {version}", version=version))

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
