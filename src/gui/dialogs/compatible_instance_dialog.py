from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout

from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.language.language_manager import tr
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.gui.dialogs.create_compatible_instance_dialog import CreateCompatibleInstanceDialog
from src.gui.mod_instance_compatibility import CompatibleModVersion, compatible_instances, normalize_supported_loader
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.instance.instance import Instance


class CompatibleInstanceDialog(QDialog):
    RUNNING_ROLE = int(Qt.ItemDataRole.UserRole) + 1

    def __init__(self, version: CompatibleModVersion, loader: str, instances: list[Instance], parent=None) -> None:
        super().__init__(parent)
        self._version = version
        self._loader = normalize_supported_loader(loader)
        self._instances = compatible_instances(instances, version, self._loader)
        self._selected_name = ""
        self._created_instance_name = ""
        self._created_game_version = ""
        self._build_ui()
        self.retranslate_dynamic()

    @property
    def selected_instance_name(self) -> str:
        return self._selected_name

    @property
    def created_instance_name(self) -> str:
        return self._created_instance_name

    @property
    def created_game_version(self) -> str:
        return self._created_game_version

    @property
    def requested_instance_creation(self) -> bool:
        return bool(self._created_instance_name and self._created_game_version)

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 760, 520, 620, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        root.addWidget(self.title_label)

        self.requirements_label = QLabel()
        self.requirements_label.setObjectName("MutedLabel")
        self.requirements_label.setWordWrap(True)
        root.addWidget(self.requirements_label)

        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.itemDoubleClicked.connect(lambda *_args: self._accept_selected())
        root.addWidget(self.table, 1)

        self.empty_label = QLabel()
        self.empty_label.setObjectName("WarningBadge")
        self.empty_label.setWordWrap(True)
        root.addWidget(self.empty_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.create_button = self.buttons.addButton(tr("mods.instance_dialog.create"), QDialogButtonBox.ButtonRole.ActionRole)
        self.create_button.clicked.connect(self._create_compatible_instance)
        self.install_button = self.buttons.addButton(tr("mods.instance_dialog.install"), QDialogButtonBox.ButtonRole.AcceptRole)
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._accept_selected)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        self._populate()

    def _populate(self) -> None:
        self.table.setRowCount(len(self._instances))
        for row, instance in enumerate(self._instances):
            loader_name, loader_version = ModLoaderManager.normalize(instance.mod_loader)
            running = InstanceRunLock.is_active(instance)
            values = [
                instance.name,
                instance.version_id,
                f"{loader_name.title()} {loader_version}".strip(),
                tr("mods.instance_dialog.running") if running else tr("mods.instance_dialog.ready"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, instance.name)
                item.setData(self.RUNNING_ROLE, running)
                self.table.setItem(row, column, item)
        if self._instances:
            self.table.selectRow(0)

    def _selection_changed(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_name = ""
            self.install_button.setEnabled(False)
            return
        item = self.table.item(rows[0].row(), 0)
        if item is None:
            self._selected_name = ""
            self.install_button.setEnabled(False)
            return
        self._selected_name = str(item.data(Qt.ItemDataRole.UserRole) or "")
        running = bool(item.data(self.RUNNING_ROLE))
        self.install_button.setEnabled(bool(self._selected_name) and not running)

    def _accept_selected(self) -> None:
        if self._selected_name and self.install_button.isEnabled():
            self.accept()

    def _create_compatible_instance(self) -> None:
        dialog = CreateCompatibleInstanceDialog(self._version, self._loader, self)
        if not dialog.exec():
            return
        self._selected_name = ""
        self._created_instance_name = dialog.instance_name
        self._created_game_version = dialog.game_version
        self.accept()

    def retranslate_dynamic(self) -> None:
        game_versions = ", ".join(self._version.game_versions[:10])
        if len(self._version.game_versions) > 10:
            game_versions += ", …"
        self.setWindowTitle(tr("mods.instance_dialog.title"))
        self.title_label.setText(tr("mods.instance_dialog.title"))
        self.requirements_label.setText(
            tr(
                "mods.instance_dialog.requirements",
                version=self._version.version_number,
                minecraft=game_versions,
                loader=self._loader.title(),
            )
        )
        self.table.setHorizontalHeaderLabels(
            [
                tr("mods.instance_dialog.column.name"),
                tr("mods.instance_dialog.column.minecraft"),
                tr("mods.instance_dialog.column.loader"),
                tr("mods.instance_dialog.column.status"),
            ]
        )
        self.empty_label.setText(
            tr("mods.instance_dialog.empty") if not self._instances else tr("mods.instance_dialog.hint")
        )
        self.empty_label.setVisible(not self._instances or any(InstanceRunLock.is_active(item) for item in self._instances))
        self.create_button.setText(tr("mods.instance_dialog.create"))
        self.install_button.setText(tr("mods.instance_dialog.install"))
