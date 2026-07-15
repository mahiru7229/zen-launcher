from __future__ import annotations

import re
from threading import Event

from PySide6.QtCore import Signal, Slot

from src.core.account.account_manager import AccountManager
from src.core.auth.microsoft.microsoft_auth_gate import MicrosoftAuthenticationLockedError
from src.core.auth.microsoft.oauth_callback_server import MicrosoftAuthorizationCancelledError
from src.core.language.language_manager import tr
from src.core.security.account_security_manager import AccountSecurityManager
from src.gui.controllers.base_controller import BaseController
from src.gui.task_runner import TaskRunner


class AccountController(BaseController):
    MICROSOFT_TASK_ID = "account.microsoft.create"
    SECURITY_AUDIT_TASK_ID = "account.security.audit"
    SECURITY_REPROTECT_TASK_ID = "account.security.reprotect"

    accounts_changed = Signal(list, str)
    selected_account_changed = Signal(object)
    microsoft_auth_state_changed = Signal(bool, str)
    security_report_changed = Signal(object)

    USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,16}$")

    def __init__(self, task_runner: TaskRunner) -> None:
        super().__init__()
        self._task_runner = task_runner
        self._microsoft_cancel_event = Event()
        self._task_runner.task_succeeded.connect(self._on_task_succeeded)
        self._task_runner.task_failed.connect(self._on_task_failed)

    def refresh(self) -> None:
        try:
            accounts = AccountManager.list_accounts()
            selected = AccountManager.get_selected_account()
        except Exception as error:
            self._emit_error(tr("Accounts"), error)
            return

        selected_id = selected.account_id if selected is not None else ""
        self.accounts_changed.emit(accounts, selected_id)
        self.selected_account_changed.emit(selected)
        self.log_created.emit(tr("Accounts refreshed: {count} found", count=len(accounts)))

    def create_offline(self, username: str) -> None:
        username = username.strip()
        if not self.USERNAME_PATTERN.fullmatch(username):
            self._emit_error(tr("Offline account"), tr("Username must contain 3-16 letters, numbers, or underscores."))
            return
        try:
            account = AccountManager.create_offline_account(username)
            AccountManager.set_selected_account(account.account_id)
        except Exception as error:
            self._emit_error(tr("Offline account"), error)
            return
        self.status_changed.emit(tr("Created offline account {username}", username=account.username))
        self.log_created.emit(tr("Offline account created: {username}", username=account.username))
        self.refresh()

    def create_microsoft(self) -> None:
        if self._task_runner.is_task_active(self.MICROSOFT_TASK_ID):
            return

        self._microsoft_cancel_event.clear()
        self.microsoft_auth_state_changed.emit(True, tr("account.microsoft.waiting"))
        started = self._task_runner.run(
            self.MICROSOFT_TASK_ID,
            lambda: AccountManager.create_microsoft_account(cancel_event=self._microsoft_cancel_event),
            tr("account.microsoft.waiting"),
            blocking=False,
        )
        if not started:
            self.microsoft_auth_state_changed.emit(False, tr("account.microsoft.status_available"))

    def cancel_microsoft(self) -> None:
        if not self._task_runner.is_task_active(self.MICROSOFT_TASK_ID):
            return
        self._microsoft_cancel_event.set()
        self.microsoft_auth_state_changed.emit(True, tr("account.microsoft.cancelling"))

    def audit_security(self) -> None:
        self._task_runner.run(
            self.SECURITY_AUDIT_TASK_ID,
            AccountSecurityManager.audit,
            tr("account.security.checking"),
            blocking=False,
        )

    def reprotect_security(self) -> None:
        self._task_runner.run(
            self.SECURITY_REPROTECT_TASK_ID,
            AccountSecurityManager.migrate_and_reprotect,
            tr("account.security.reprotecting"),
            blocking=True,
        )

    def select(self, account_id: str) -> None:
        if not account_id:
            return
        try:
            updated = AccountManager.set_selected_account(account_id)
            if updated is False:
                raise RuntimeError(tr("The selected account could not be saved."))
        except Exception as error:
            self._emit_error(tr("Select account"), error)
            return
        self.status_changed.emit(tr("Selected account updated"))
        self.refresh()

    def remove(self, account_id: str) -> None:
        if not account_id:
            return
        try:
            removed = AccountManager.remove_account(account_id)
            if not removed:
                raise RuntimeError(tr("Account was not found."))
        except Exception as error:
            self._emit_error(tr("Remove account"), error)
            return
        self.status_changed.emit(tr("Account removed"))
        self.log_created.emit(tr("Account removed: {account_id}", account_id=account_id))
        self.refresh()

    @Slot(str, object)
    def _on_task_succeeded(self, task_id: str, result: object) -> None:
        if task_id == self.SECURITY_AUDIT_TASK_ID:
            self.security_report_changed.emit(result)
            return
        if task_id == self.SECURITY_REPROTECT_TASK_ID:
            self.security_report_changed.emit(result)
            self.status_changed.emit(tr("account.security.reprotected"))
            self.log_created.emit(tr("account.security.reprotected"))
            self.refresh()
            return
        if task_id != self.MICROSOFT_TASK_ID:
            return

        self._microsoft_cancel_event.clear()
        self.microsoft_auth_state_changed.emit(False, tr("account.microsoft.status_available"))
        account = result
        username = str(getattr(account, "username", ""))
        self.status_changed.emit(tr("account.microsoft.added", username=username))
        self.log_created.emit(tr("account.microsoft.added", username=username))
        self.refresh()

    @Slot(str, object)
    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id in {self.SECURITY_AUDIT_TASK_ID, self.SECURITY_REPROTECT_TASK_ID}:
            self._emit_error(tr("account.security.title"), error)
            return
        if task_id != self.MICROSOFT_TASK_ID:
            return

        self._microsoft_cancel_event.clear()
        self.microsoft_auth_state_changed.emit(False, tr("account.microsoft.status_available"))

        if isinstance(error, MicrosoftAuthorizationCancelledError):
            self.status_changed.emit(tr("account.microsoft.cancelled"))
            self.log_created.emit(tr("account.microsoft.cancelled"))
            return

        if isinstance(error, MicrosoftAuthenticationLockedError):
            self._emit_error(tr("account.microsoft.title"), error)
            return

        self._emit_error(tr("account.microsoft.title"), error)
