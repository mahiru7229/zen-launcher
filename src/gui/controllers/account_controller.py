from __future__ import annotations

import re

from PySide6.QtCore import Signal

from src.core.account.account_manager import AccountManager
from src.core.auth.microsoft.microsoft_auth_gate import MicrosoftAuthenticationLockedError
from src.core.language.language_manager import tr
from src.gui.controllers.base_controller import BaseController


class AccountController(BaseController):
    accounts_changed = Signal(list, str)
    selected_account_changed = Signal(object)

    USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,16}$")

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
        try:
            account = AccountManager.create_microsoft_account()
        except MicrosoftAuthenticationLockedError:
            self._emit_error(tr("Microsoft account"), RuntimeError(tr("Microsoft account sign-in is prepared but locked while MCW Launcher waits for Mojang/Microsoft application approval.")))
            return
        except Exception as error:
            self._emit_error(tr("Microsoft account"), error)
            return
        self.status_changed.emit(tr("Microsoft account added: {username}", username=account.username))
        self.log_created.emit(tr("Microsoft account added: {username}", username=account.username))
        self.refresh()

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
