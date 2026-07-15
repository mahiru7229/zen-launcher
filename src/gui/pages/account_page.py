from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from src.core.language.language_manager import tr
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget
from src.gui.theme.runtime import set_theme_icon


class AccountPage(BasePage):
    create_offline_requested = Signal(str)
    create_microsoft_requested = Signal()
    select_requested = Signal(str)
    remove_requested = Signal(str)
    refresh_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Accounts", "Manage offline accounts. Microsoft sign-in is prepared but remains locked until application approval is granted.", "accounts")
        self._accounts: dict[str, object] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        selected_card = CardWidget("Saved accounts")
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self._update_details)
        self.username_value = QLabel("Username: -")
        self.username_value.setObjectName("ValueLabel")
        self.type_value = QLabel("Type: -")
        self.type_value.setObjectName("MutedLabel")
        self.uuid_value = QLabel("UUID: -")
        self.uuid_value.setObjectName("TinyLabel")
        self.uuid_value.setWordWrap(True)

        action_grid = QGridLayout()
        select_button = set_theme_icon(QPushButton("Use selected account"), "icon.action.account")
        select_button.setObjectName("PrimaryButton")
        remove_button = set_theme_icon(QPushButton("Remove"), "icon.action.remove")
        remove_button.setObjectName("DangerButton")
        refresh_button = set_theme_icon(QPushButton("Refresh"), "icon.action.refresh")
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

        create_card = CardWidget("Create offline account", "Minecraft usernames use 3-16 letters, numbers, or underscores.")
        create_card.setProperty("themeRole", "microsoft")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Example: Steve")
        create_button = set_theme_icon(QPushButton("Create and select"), "icon.action.add")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(lambda: self.create_offline_requested.emit(self.username_input.text()))
        self.microsoft_button = set_theme_icon(QPushButton("Add Microsoft account — approval pending"), "icon.action.microsoft")
        self.microsoft_button.setToolTip("The authentication pipeline is prepared, but sign-in is locked until Mojang/Microsoft approves the launcher application.")
        self.microsoft_button.clicked.connect(self.create_microsoft_requested.emit)
        self.microsoft_status = QLabel("Microsoft authentication status: Pending application approval")
        self.microsoft_status.setObjectName("LockedBadge")
        self.microsoft_status.setWordWrap(True)
        create_card.layout.addWidget(QLabel("Username"))
        create_card.layout.addWidget(self.username_input)
        create_card.layout.addWidget(create_button)
        create_card.layout.addWidget(self.microsoft_button)
        create_card.layout.addWidget(self.microsoft_status)
        self.root_layout.addWidget(create_card)
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
        self._update_details()
