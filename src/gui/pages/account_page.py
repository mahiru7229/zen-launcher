from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from src.core.language.language_manager import tr
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget


class AccountPage(BasePage):
    create_offline_requested = Signal(str)
    create_microsoft_requested = Signal()
    cancel_microsoft_requested = Signal()
    select_requested = Signal(str)
    remove_requested = Signal(str)
    refresh_requested = Signal()
    security_audit_requested = Signal()
    security_reprotect_requested = Signal()

    def __init__(self) -> None:
        super().__init__(tr("Accounts"), tr("account.page.subtitle"), "accounts")
        self._accounts: dict[str, object] = {}
        self._microsoft_auth_active = False
        self._microsoft_status_override = ""
        self._build_ui()

    def _build_ui(self) -> None:
        selected_card = CardWidget(tr("Saved accounts"))
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self._update_details)
        self.username_value = QLabel(tr("Username: -"))
        self.username_value.setObjectName("ValueLabel")
        self.type_value = QLabel(tr("Type: -"))
        self.type_value.setObjectName("MutedLabel")
        self.uuid_value = QLabel(tr("UUID: -"))
        self.uuid_value.setObjectName("TinyLabel")
        self.uuid_value.setWordWrap(True)

        action_grid = QGridLayout()
        select_button = set_theme_icon(QPushButton(tr("Use selected account")), "icon.action.account")
        select_button.setObjectName("PrimaryButton")
        remove_button = set_theme_icon(QPushButton(tr("Remove")), "icon.action.remove")
        remove_button.setObjectName("DangerButton")
        refresh_button = set_theme_icon(QPushButton(tr("Refresh")), "icon.action.refresh")
        select_button.clicked.connect(lambda: self.select_requested.emit(self.current_account_id()))
        remove_button.clicked.connect(self._confirm_remove)
        refresh_button.clicked.connect(self.refresh_requested.emit)
        action_grid.addWidget(select_button, 0, 0, 1, 2)
        action_grid.addWidget(remove_button, 1, 0)
        action_grid.addWidget(refresh_button, 1, 1)

        selected_card.layout.addWidget(self.account_combo)
        selected_card.layout.addWidget(self.username_value)
        selected_card.layout.addWidget(self.type_value)
        selected_card.layout.addWidget(self.uuid_value)
        selected_card.layout.addLayout(action_grid)
        self.root_layout.addWidget(selected_card)

        create_card = CardWidget(tr("account.create.title"), tr("account.create.description"))
        create_card.setProperty("themeRole", "microsoft")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("Example: Steve"))
        create_button = set_theme_icon(QPushButton(tr("Create and select")), "icon.action.add")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(lambda: self.create_offline_requested.emit(self.username_input.text()))

        self.microsoft_button = set_theme_icon(QPushButton(tr("account.microsoft.add")), "icon.action.microsoft")
        self.microsoft_button.setToolTip(tr("account.microsoft.tooltip"))
        self.microsoft_button.clicked.connect(self.create_microsoft_requested.emit)

        self.microsoft_cancel_button = set_theme_icon(QPushButton(tr("account.microsoft.cancel")), "icon.action.remove")
        self.microsoft_cancel_button.setObjectName("DangerButton")
        self.microsoft_cancel_button.clicked.connect(self.cancel_microsoft_requested.emit)
        self.microsoft_cancel_button.setVisible(False)

        self.microsoft_status = QLabel(tr("account.microsoft.status_available"))
        self.microsoft_status.setObjectName("StatusBadge")
        self.microsoft_status.setWordWrap(True)

        create_card.layout.addWidget(QLabel(tr("Username")))
        create_card.layout.addWidget(self.username_input)
        create_card.layout.addWidget(create_button)
        create_card.layout.addWidget(self.microsoft_button)
        create_card.layout.addWidget(self.microsoft_cancel_button)
        create_card.layout.addWidget(self.microsoft_status)
        self.root_layout.addWidget(create_card)

        security_card = CardWidget(tr("account.security.title"), tr("account.security.description"))
        security_card.setProperty("themeRole", "security")
        self.security_status = QLabel(tr("account.security.checking"))
        self.security_status.setObjectName("StatusBadge")
        self.security_status.setWordWrap(True)
        security_buttons = QGridLayout()
        verify_button = set_theme_icon(QPushButton(tr("account.security.verify")), "icon.action.shield")
        reprotect_button = set_theme_icon(QPushButton(tr("account.security.reprotect")), "icon.action.reprotect")
        verify_button.clicked.connect(self.security_audit_requested.emit)
        reprotect_button.clicked.connect(self.security_reprotect_requested.emit)
        security_buttons.addWidget(verify_button, 0, 0)
        security_buttons.addWidget(reprotect_button, 0, 1)
        security_card.layout.addWidget(self.security_status)
        security_card.layout.addLayout(security_buttons)
        self.root_layout.addWidget(security_card)
        self.root_layout.addStretch()

    def set_accounts(self, accounts: list, selected_id: str) -> None:
        self._accounts = {account.account_id: account for account in accounts}
        self.account_combo.blockSignals(True)
        self.account_combo.clear()
        for account in accounts:
            account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
            self.account_combo.addItem(f"{account.username}  [{account_type}]", account.account_id)
        if selected_id:
            index = self.account_combo.findData(selected_id)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
        self.account_combo.blockSignals(False)
        self._update_details()

    def current_account_id(self) -> str:
        return str(self.account_combo.currentData() or "")

    def set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)

    def set_microsoft_auth_state(self, active: bool, message: str = "") -> None:
        self._microsoft_auth_active = bool(active)
        self._microsoft_status_override = str(message or "")
        self.microsoft_button.setEnabled(not active)
        self.microsoft_cancel_button.setVisible(active)
        self.microsoft_cancel_button.setEnabled(active and message != tr("account.microsoft.cancelling"))
        self.microsoft_status.setObjectName("WarningBadge" if active else "StatusBadge")
        self.microsoft_status.setText(self._microsoft_status_override or tr("account.microsoft.status_available"))
        self.microsoft_status.style().unpolish(self.microsoft_status)
        self.microsoft_status.style().polish(self.microsoft_status)


    def set_security_report(self, report: object) -> None:
        healthy = bool(getattr(report, "is_healthy", False))
        self.security_status.setObjectName("StatusBadge" if healthy else "WarningBadge")
        self.security_status.setText(
            tr(
                "account.security.summary",
                protected=getattr(report, "protected_account_count", 0),
                microsoft=getattr(report, "microsoft_account_count", 0),
                legacy=getattr(report, "legacy_account_count", 0),
                invalid=getattr(report, "invalid_account_count", 0),
            )
        )
        self.security_status.style().unpolish(self.security_status)
        self.security_status.style().polish(self.security_status)

    def _update_details(self) -> None:
        account = self._accounts.get(self.current_account_id())
        if account is None:
            self.username_value.setText(tr("Username: -"))
            self.type_value.setText(tr("Type: -"))
            self.uuid_value.setText(tr("UUID: -"))
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.username_value.setText(tr("Username: {username}", username=account.username))
        self.type_value.setText(tr("Type: {account_type}", account_type=account_type.upper()))
        self.uuid_value.setText(tr("UUID: {uuid}", uuid=account.uuid))

    def _confirm_remove(self) -> None:
        account_id = self.current_account_id()
        if not account_id:
            return
        account = self._accounts.get(account_id)
        username = getattr(account, "username", tr("this account"))
        answer = QMessageBox.question(self, tr("Remove account"), tr("Remove '{username}' from the launcher?", username=username), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(account_id)

    def retranslate_dynamic(self) -> None:
        self.microsoft_button.setText(tr("account.microsoft.add"))
        self.microsoft_button.setToolTip(tr("account.microsoft.tooltip"))
        self.microsoft_cancel_button.setText(tr("account.microsoft.cancel"))
        if not self._microsoft_auth_active:
            self._microsoft_status_override = ""
        self.set_microsoft_auth_state(self._microsoft_auth_active, self._microsoft_status_override)
        self._update_details()
