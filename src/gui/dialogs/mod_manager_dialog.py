from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.models.instance.instance import Instance
from src.models.mod.mod_info import ModInfo


class ModManagerDialog(QDialog):
    refresh_requested = Signal()
    add_requested = Signal(list, bool)
    remove_requested = Signal(list)
    enabled_requested = Signal(list, bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._mods: list[ModInfo] = []
        self.setWindowTitle("Mod Manager")
        self.resize(1050, 680)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel("No instance selected")
        self.title_label.setObjectName("PageTitle")
        self.summary_label = QLabel("Choose a Fabric instance to manage its mods.")
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.summary_label)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name, mod id, version, or file...")
        self.search_input.textChanged.connect(self._apply_filter)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        open_folder_button = QPushButton("Open mod folder")
        open_folder_button.clicked.connect(self._open_folder)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(refresh_button)
        search_row.addWidget(open_folder_button)
        root.addLayout(search_row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["State", "Name", "Version", "Mod ID", "Environment", "Status", "File"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._render_details)
        root.addWidget(self.table, 1)

        action_row = QHBoxLayout()
        self.add_button = QPushButton("Add mod files")
        self.add_button.setObjectName("PrimaryButton")
        self.enable_button = QPushButton("Enable")
        self.disable_button = QPushButton("Disable")
        self.remove_button = QPushButton("Remove")
        self.remove_button.setObjectName("DangerButton")
        self.add_button.clicked.connect(self._choose_add)
        self.enable_button.clicked.connect(lambda: self._request_enabled(True))
        self.disable_button.clicked.connect(lambda: self._request_enabled(False))
        self.remove_button.clicked.connect(self._request_remove)
        action_row.addWidget(self.add_button)
        action_row.addWidget(self.enable_button)
        action_row.addWidget(self.disable_button)
        action_row.addWidget(self.remove_button)
        action_row.addStretch()
        root.addLayout(action_row)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a mod to view metadata and dependencies.")
        self.details.setMaximumHeight(170)
        root.addWidget(self.details)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._mods = []
        self.table.setRowCount(0)
        self.details.clear()

        if instance is None:
            self.title_label.setText("No instance selected")
            self.summary_label.setText("Choose a Fabric instance to manage its mods.")
            self._set_actions_enabled(False)
            return

        loader_name, loader_version = ModLoaderManager.normalize(instance.mod_loader)
        self.title_label.setText(f"Mods — {instance.name}")
        if loader_name == ModLoaderManager.FABRIC:
            self.summary_label.setText(f"Minecraft {instance.version_id} • Fabric Loader {loader_version} • Drop .jar files into this window to add them.")
            self._set_actions_enabled(True)
        else:
            self.summary_label.setText("This instance is Vanilla. Apply Fabric Loader from the Instances page before adding mods.")
            self._set_actions_enabled(False)

    def set_mods(self, mods: list[ModInfo]) -> None:
        self._mods = list(mods)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._mods))

        for row, mod in enumerate(self._mods):
            values = ["Enabled" if mod.enabled else "Disabled", mod.name, mod.version, mod.mod_id, mod.environment, mod.status, mod.file_name]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, mod)
                if mod.error:
                    item.setToolTip(mod.error)
                self.table.setItem(row, column, item)

        self.table.setSortingEnabled(True)
        self._apply_filter()
        enabled_count = sum(1 for mod in self._mods if mod.enabled)
        if self._instance is not None and self._is_fabric_instance():
            self.summary_label.setText(f"{len(self._mods)} mod(s) found • {enabled_count} enabled • {self._instance.instance_dir / 'mods'}")

    def set_busy(self, busy: bool) -> None:
        enabled = not busy and self._is_fabric_instance()
        self._set_actions_enabled(enabled)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        paths = self._jar_paths_from_urls(event.mimeData().urls())
        if paths and self._is_fabric_instance():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._jar_paths_from_urls(event.mimeData().urls())
        if paths and self._is_fabric_instance():
            self._request_add(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _choose_add(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Add Fabric mods", "", "Fabric mods (*.jar)")
        if files:
            self._request_add([Path(file) for file in files])

    def _request_add(self, paths: list[Path]) -> None:
        existing_names = {mod.file_name.casefold() for mod in self._mods}
        conflicts = [path.name for path in paths if path.name.casefold() in existing_names]
        replace = False

        if conflicts:
            answer = QMessageBox.question(self, "Replace mods", "The following files already exist:\n\n" + "\n".join(conflicts) + "\n\nReplace them?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            replace = True

        self.add_requested.emit(paths, replace)

    def _request_remove(self) -> None:
        paths = self._selected_paths()
        if not paths:
            return
        answer = QMessageBox.question(self, "Remove mods", f"Remove {len(paths)} selected mod file(s)?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(paths)

    def _request_enabled(self, enabled: bool) -> None:
        paths = self._selected_paths()
        if paths:
            self.enabled_requested.emit(paths, enabled)

    def _selected_paths(self) -> list[Path]:
        paths: list[Path] = []
        for index in self.table.selectionModel().selectedRows():
            item = self.table.item(index.row(), 0)
            mod = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
            if isinstance(mod, ModInfo):
                paths.append(mod.path)
        return paths

    def _render_details(self) -> None:
        selected = self._selected_paths()
        if not selected:
            self.details.clear()
            return

        mod = next((item for item in self._mods if item.path == selected[0]), None)
        if mod is None:
            return

        dependencies = "\n".join(f"  {name}: {requirement}" for name, requirement in mod.dependencies.items()) or "  None declared"
        authors = ", ".join(mod.authors) or "Unknown"
        licenses = ", ".join(mod.licenses) or "Unknown"
        text = [
            f"{mod.name} ({mod.mod_id})",
            f"Version: {mod.version}",
            f"State: {'Enabled' if mod.enabled else 'Disabled'}",
            f"Environment: {mod.environment}",
            f"Authors: {authors}",
            f"License: {licenses}",
            f"Status: {mod.status}",
            "",
            mod.description or "No description.",
            "",
            "Dependencies:",
            dependencies,
        ]
        if mod.error:
            text.extend(["", "Warning:", mod.error])
        self.details.setPlainText("\n".join(text))

    def _apply_filter(self) -> None:
        query = self.search_input.text().strip().casefold()
        for row, mod in enumerate(self._mods):
            haystack = " ".join((mod.name, mod.mod_id, mod.version, mod.file_name, mod.status)).casefold()
            self.table.setRowHidden(row, bool(query and query not in haystack))

    def _open_folder(self) -> None:
        if self._instance is not None:
            folder = self._instance.instance_dir / "mods"
            folder.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def _set_actions_enabled(self, enabled: bool) -> None:
        self.add_button.setEnabled(enabled)
        self.enable_button.setEnabled(enabled)
        self.disable_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)

    def _is_fabric_instance(self) -> bool:
        if self._instance is None:
            return False
        loader_name, _ = ModLoaderManager.normalize(self._instance.mod_loader)
        return loader_name == ModLoaderManager.FABRIC

    @staticmethod
    def _jar_paths_from_urls(urls: list[QUrl]) -> list[Path]:
        paths = [Path(url.toLocalFile()) for url in urls if url.isLocalFile()]
        return [path for path in paths if path.is_file() and path.suffix.lower() == ".jar"]
