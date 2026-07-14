from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.gui.config import MAIN_LOGO_PATH, VERSION
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class HomePage(BasePage):
    manage_accounts_requested = Signal()
    manage_instances_requested = Signal()
    open_settings_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Home", "Your launch deck: current account, active instance, and core status in one place.")
        self._build_ui()

    def _build_ui(self) -> None:
        hero = CardWidget("", object_name="HeroCard")
        hero_layout = QVBoxLayout()
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(MAIN_LOGO_PATH))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("MCW")
            logo.setObjectName("BrandLabel")

        hero_title = QLabel("MCW LAUNCHER")
        hero_title.setObjectName("PageTitle")
        hero_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_version = QLabel(VERSION)
        hero_version.setObjectName("MutedLabel")
        hero_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(logo)
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_version)
        hero.layout.addLayout(hero_layout)
        self.root_layout.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        account_card = CardWidget("Active account", "The account used for the next launch.")
        self.account_value = QLabel("No account selected")
        self.account_value.setObjectName("ValueLabel")
        self.account_detail = QLabel("Open Accounts to create an offline account.")
        self.account_detail.setObjectName("MutedLabel")
        account_button = QPushButton("Open Accounts")
        account_button.clicked.connect(self.manage_accounts_requested.emit)
        account_card.layout.addWidget(self.account_value)
        account_card.layout.addWidget(self.account_detail)
        account_card.layout.addWidget(account_button)

        instance_card = CardWidget("Active instance", "The instance attached to the permanent launch bar.")
        self.instance_value = QLabel("No instance selected")
        self.instance_value.setObjectName("ValueLabel")
        self.instance_detail = QLabel("Open Instances to create or choose one.")
        self.instance_detail.setObjectName("MutedLabel")
        instance_button = QPushButton("Open Instances")
        instance_button.clicked.connect(self.manage_instances_requested.emit)
        instance_card.layout.addWidget(self.instance_value)
        instance_card.layout.addWidget(self.instance_detail)
        instance_card.layout.addWidget(instance_button)

        core_card = CardWidget("Core connection", "GUI only calls the public MCW Core API.")
        self.manifest_value = QLabel("Manifest not loaded")
        self.manifest_value.setObjectName("ValueLabel")
        self.last_status = QLabel("Ready")
        self.last_status.setObjectName("MutedLabel")
        settings_button = QPushButton("Launcher Settings")
        settings_button.clicked.connect(self.open_settings_requested.emit)
        core_card.layout.addWidget(self.manifest_value)
        core_card.layout.addWidget(self.last_status)
        core_card.layout.addWidget(settings_button)

        grid.addWidget(account_card, 0, 0)
        grid.addWidget(instance_card, 0, 1)
        grid.addWidget(core_card, 1, 0, 1, 2)
        self.root_layout.addLayout(grid)
        self.root_layout.addStretch()

    def set_account(self, account: object | None) -> None:
        if account is None:
            self.account_value.setText("No account selected")
            self.account_detail.setText("Open Accounts to create an offline account.")
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.account_value.setText(account.username)
        self.account_detail.setText(account_type.upper())

    def set_instance(self, instance: object | None) -> None:
        if instance is None:
            self.instance_value.setText("No instance selected")
            self.instance_detail.setText("Open Instances to create or choose one.")
            return
        self.instance_value.setText(instance.name)
        self.instance_detail.setText(f"Minecraft {instance.version_id}")

    def set_manifest_count(self, count: int) -> None:
        self.manifest_value.setText(f"{count} versions available")

    def set_status(self, message: str) -> None:
        self.last_status.setText(message)
