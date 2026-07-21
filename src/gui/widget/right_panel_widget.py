from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from src.core.language.language_manager import tr
from src.gui.widget.card_widget import CardWidget
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap


class RightPanelWidget(QFrame):
    manage_accounts_requested = Signal()
    manage_instances_requested = Signal()
    manage_mods_requested = Signal(str)
    refresh_requested = Signal()

    MAX_RUNNING_INSTANCES = 4

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("RightPanel")
        self._instance_name = ""
        self._account: object | None = None
        self._instance: object | None = None
        self._running_instances: list[object] = []
        self._busy = False
        self._status_message = "Waiting for a task."
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
        account_button = set_theme_icon(QPushButton("Manage accounts"), "icon.action.account")
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
        instance_button = set_theme_icon(QPushButton("Manage instances"), "icon.action.instance")
        instance_button.clicked.connect(self.manage_instances_requested.emit)
        self.manage_mods_button = set_theme_icon(QPushButton("Manage mods"), "icon.action.mods")
        self.manage_mods_button.setEnabled(False)
        self.manage_mods_button.clicked.connect(lambda: self.manage_mods_requested.emit(self._instance_name))
        self.instance_card.layout.addWidget(self.instance_name)
        self.instance_card.layout.addWidget(self.instance_version)
        self.instance_card.layout.addWidget(self.instance_loader)
        self.instance_card.layout.addWidget(self.instance_path)
        self.instance_card.layout.addWidget(instance_button)
        self.instance_card.layout.addWidget(self.manage_mods_button)
        layout.addWidget(self.instance_card)

        self.running_card = CardWidget("Running instances")
        self.running_count = QLabel("No instances running")
        self.running_count.setObjectName("ValueLabel")
        self.running_list = QLabel("Minecraft sessions will appear here.")
        self.running_list.setObjectName("TinyLabel")
        self.running_list.setWordWrap(True)
        self.running_card.layout.addWidget(self.running_count)
        self.running_card.layout.addWidget(self.running_list)
        layout.addWidget(self.running_card)

        status_card = CardWidget("Launcher state")
        self.status_icon = set_theme_pixmap(QLabel(), "icon.state.ready", 32, 32)
        self.status_badge = QLabel("READY")
        self.status_badge.setObjectName("StatusBadge")
        self.status_text = QLabel("Waiting for a task.")
        self.status_text.setObjectName("MutedLabel")
        self.status_text.setWordWrap(True)
        refresh_button = set_theme_icon(QPushButton("Refresh data"), "icon.action.refresh")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        status_card.layout.addWidget(self.status_icon)
        status_card.layout.addWidget(self.status_badge)
        status_card.layout.addWidget(self.status_text)
        status_card.layout.addWidget(refresh_button)
        layout.addWidget(status_card)
        layout.addStretch()

    def set_account(self, account: object | None) -> None:
        self._account = account
        if account is None:
            self.account_name.setText(tr("No account selected"))
            self.account_type.setText(tr("Create an offline account to continue."))
            self.account_uuid.setText(tr("UUID: -"))
            return
        account_type = getattr(getattr(account, "account_type", None), "value", "unknown")
        self.account_name.setText(account.username)
        self.account_type.setText(account_type.upper())
        self.account_uuid.setText(tr("UUID: {uuid}", uuid=account.uuid))

    def set_instance(self, instance: object | None) -> None:
        self._instance = instance
        if instance is None:
            self._instance_name = ""
            self.manage_mods_button.setEnabled(False)
            self.manage_mods_button.setToolTip(tr("right_panel.mods.select_modded"))
            self.instance_name.setText(tr("No instance selected"))
            self.instance_version.setText(tr("Minecraft: -"))
            self.instance_loader.setText(tr("Loader: -"))
            self.instance_path.setText(tr("Path: -"))
            return
        self._instance_name = str(instance.name)
        loader = getattr(instance, "mod_loader", ("vanilla", "-1"))
        loader_name = loader[0] if loader else "vanilla"
        loader_version = loader[1] if len(loader) > 1 else "-1"
        loader_text = loader_name if loader_version in {"", "-1"} else f"{loader_name} {loader_version}"
        is_modded = str(loader_name).casefold() in {"fabric", "forge"}
        self.manage_mods_button.setEnabled(is_modded)
        self.manage_mods_button.setToolTip("" if is_modded else tr("right_panel.mods.apply_loader"))
        self.instance_name.setText(instance.name)
        self.instance_version.setText(tr("Minecraft: {version}", version=instance.version_id))
        self.instance_loader.setText(tr("Loader: {loader}", loader=loader_text))
        self.instance_path.setText(tr("Path: {path}", path=Path(instance.instance_dir)))

    def set_running_instances(self, running_instances: list[object]) -> None:
        self._running_instances = list(running_instances)
        count = len(running_instances)

        if count == 0:
            self.running_count.setText(tr("No instances running"))
            self.running_list.setText(tr("Minecraft sessions will appear here."))
            return

        count_key = "{count} instance running" if count == 1 else "{count} instances running"
        self.running_count.setText(tr(count_key, count=count))

        lines = []
        for running_instance in running_instances[:self.MAX_RUNNING_INSTANCES]:
            name = str(getattr(running_instance, "name", tr("Unknown instance")))
            state_key = str(getattr(running_instance, "state", "running")).replace("_", " ")
            state = tr(state_key).title()
            lines.append(f"• {name} — {state}")

        hidden_count = count - self.MAX_RUNNING_INSTANCES
        if hidden_count > 0:
            lines.append(tr("+ {count} more", count=hidden_count))

        self.running_list.setText("\n".join(lines))

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        set_theme_pixmap(self.status_icon, "icon.state.busy" if busy else "icon.state.ready", 32, 32)
        self.status_badge.setText(tr("BUSY" if busy else "READY"))
        self.status_badge.setObjectName("WarningBadge" if busy else "StatusBadge")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def set_status(self, message: str) -> None:
        self._status_message = message
        self.status_text.setText(tr(message))

    def retranslate_dynamic(self) -> None:
        self.set_account(self._account)
        self.set_instance(self._instance)
        self.set_running_instances(self._running_instances)
        self.set_busy(self._busy)
        self.status_text.setText(tr(self._status_message))
