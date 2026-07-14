from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class AccountPage(BasePage):
    create_offline_requested = Signal(str)
    select_requested = Signal(str)
    remove_requested = Signal(str)
    refresh_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Accounts", "Store offline accounts now; Microsoft authentication can be plugged into this page later.")
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
        select_button = QPushButton("Use selected account")
        select_button.setObjectName("PrimaryButton")
        remove_button = QPushButton("Remove")
        remove_button.setObjectName("DangerButton")
        refresh_button = QPushButton("Refresh")
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
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Example: Steve")
        create_button = QPushButton("Create and select")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(lambda: self.create_offline_requested.emit(self.username_input.text()))
        microsoft_button = QPushButton("Microsoft account — in progress")
        microsoft_button.setEnabled(False)
        create_card.layout.addWidget(QLabel("Username"))
        create_card.layout.addWidget(self.username_input)
        create_card.layout.addWidget(create_button)
        create_card.layout.addWidget(microsoft_button)
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
            self.username_value.setText("Username: -")
            self.type_value.setText("Type: -")
            self.uuid_value.setText("UUID: -")
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.username_value.setText(f"Username: {account.username}")
        self.type_value.setText(f"Type: {account_type.upper()}")
        self.uuid_value.setText(f"UUID: {account.uuid}")

    def _confirm_remove(self) -> None:
        account_id = self.current_account_id()
        if not account_id:
            return
        account = self._accounts.get(account_id)
        username = getattr(account, "username", "this account")
        answer = QMessageBox.question(self, "Remove account", f"Remove '{username}' from the launcher?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(account_id)
