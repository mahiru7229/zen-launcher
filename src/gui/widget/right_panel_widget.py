from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from src.gui.widget.card_widget import CardWidget


class RightPanelWidget(QFrame):
    manage_accounts_requested = Signal()
    manage_instances_requested = Signal()
    refresh_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("RightPanel")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(14)

        title = QLabel("SESSION")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        self.account_card = CardWidget("Active account")
        self.account_name = QLabel("No account selected")
        self.account_name.setObjectName("ValueLabel")
        self.account_type = QLabel("Create an offline account to continue.")
        self.account_type.setObjectName("MutedLabel")
        self.account_uuid = QLabel("UUID: -")
        self.account_uuid.setObjectName("TinyLabel")
        self.account_uuid.setWordWrap(True)
        account_button = QPushButton("Manage accounts")
        account_button.clicked.connect(self.manage_accounts_requested.emit)
        self.account_card.layout.addWidget(self.account_name)
        self.account_card.layout.addWidget(self.account_type)
        self.account_card.layout.addWidget(self.account_uuid)
        self.account_card.layout.addWidget(account_button)
        layout.addWidget(self.account_card)

        self.instance_card = CardWidget("Active instance")
        self.instance_name = QLabel("No instance selected")
        self.instance_name.setObjectName("ValueLabel")
        self.instance_version = QLabel("Minecraft: -")
        self.instance_version.setObjectName("MutedLabel")
        self.instance_loader = QLabel("Loader: -")
        self.instance_loader.setObjectName("MutedLabel")
        self.instance_path = QLabel("Path: -")
        self.instance_path.setObjectName("TinyLabel")
        self.instance_path.setWordWrap(True)
        instance_button = QPushButton("Manage instances")
        instance_button.clicked.connect(self.manage_instances_requested.emit)
        self.instance_card.layout.addWidget(self.instance_name)
        self.instance_card.layout.addWidget(self.instance_version)
        self.instance_card.layout.addWidget(self.instance_loader)
        self.instance_card.layout.addWidget(self.instance_path)
        self.instance_card.layout.addWidget(instance_button)
        layout.addWidget(self.instance_card)

        status_card = CardWidget("Launcher state")
        self.status_badge = QLabel("READY")
        self.status_badge.setObjectName("StatusBadge")
        self.status_text = QLabel("Waiting for a task.")
        self.status_text.setObjectName("MutedLabel")
        self.status_text.setWordWrap(True)
        refresh_button = QPushButton("Refresh data")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        status_card.layout.addWidget(self.status_badge)
        status_card.layout.addWidget(self.status_text)
        status_card.layout.addWidget(refresh_button)
        layout.addWidget(status_card)
        layout.addStretch()

    def set_account(self, account: object | None) -> None:
        if account is None:
            self.account_name.setText("No account selected")
            self.account_type.setText("Create an offline account to continue.")
            self.account_uuid.setText("UUID: -")
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.account_name.setText(account.username)
        self.account_type.setText(account_type.upper())
        self.account_uuid.setText(f"UUID: {account.uuid}")

    def set_instance(self, instance: object | None) -> None:
        if instance is None:
            self.instance_name.setText("No instance selected")
            self.instance_version.setText("Minecraft: -")
            self.instance_loader.setText("Loader: -")
            self.instance_path.setText("Path: -")
            return
        loader = getattr(instance, "mod_loader", ("vanilla", "-1"))
        loader_name = loader[0] if loader else "vanilla"
        loader_version = loader[1] if len(loader) > 1 else "-1"
        loader_text = loader_name if loader_version in {"", "-1"} else f"{loader_name} {loader_version}"
        self.instance_name.setText(instance.name)
        self.instance_version.setText(f"Minecraft: {instance.version_id}")
        self.instance_loader.setText(f"Loader: {loader_text}")
        self.instance_path.setText(f"Path: {Path(instance.instance_dir)}")

    def set_busy(self, busy: bool) -> None:
        self.status_badge.setText("BUSY" if busy else "READY")
        self.status_badge.setObjectName("WarningBadge" if busy else "StatusBadge")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def set_status(self, message: str) -> None:
        self.status_text.setText(message)
