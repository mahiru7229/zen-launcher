from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from src.core.instance.instance_manager import InstanceManager
from src.core.language.language_manager import tr
from src.models.instance.instance import Instance
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthVersion


class ModrinthBrowserDialog(QDialog):
    search_requested = Signal(str, str, str, int)
    versions_requested = Signal(str, str, str)
    install_mod_requested = Signal(str)
    install_modpack_requested = Signal(str, str, str, bool)

    PAGE_SIZE = 25

    def __init__(self, project_type: str, parent=None) -> None:
        super().__init__(parent)
        self.project_type = project_type
        self._instance: Instance | None = None
        self._result: ModrinthSearchResult | None = None
        self._projects: list[ModrinthProject] = []
        self._versions: list[ModrinthVersion] = []
        self._selected_project: ModrinthProject | None = None
        self._offset = 0
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        self._build_ui()
        self.retranslate_dynamic()

    def _build_ui(self) -> None:
        self.resize(1120, 720)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.context_label = QLabel()
        self.context_label.setObjectName("MutedLabel")
        self.context_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.context_label)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._request_search)
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Relevance", "relevance")
        self.sort_combo.addItem("Downloads", "downloads")
        self.sort_combo.addItem("Recently updated", "updated")
        self.sort_combo.addItem("Newest", "newest")
        self.search_button = QPushButton()
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        self.results_table = QTableWidget(0, 5)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.itemSelectionChanged.connect(self._project_selected)
        root.addWidget(self.results_table, 1)

        page_row = QHBoxLayout()
        self.result_count_label = QLabel()
        self.result_count_label.setObjectName("MutedLabel")
        self.previous_button = QPushButton()
        self.next_button = QPushButton()
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        page_row.addWidget(self.result_count_label)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        root.addLayout(page_row)

        selection_row = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.instance_name_input = QLineEdit()
        self.instance_name_input.textEdited.connect(self._instance_name_edited)
        self.optional_checkbox = QCheckBox()
        self.optional_checkbox.setChecked(True)
        self.install_button = QPushButton()
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        selection_row.addWidget(self.version_combo, 2)
        if self.project_type == "modpack":
            selection_row.addWidget(self.instance_name_input, 2)
            selection_row.addWidget(self.optional_checkbox)
        selection_row.addWidget(self.install_button)
        root.addLayout(selection_row)

        self.details_label = QLabel()
        self.details_label.setWordWrap(True)
        self.details_label.setObjectName("MutedLabel")
        self.details_label.setMinimumHeight(70)
        root.addWidget(self.details_label)

    @property
    def game_version(self) -> str:
        return self._instance.version_id if self._instance is not None else ""

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._offset = 0
        self._result = None
        self._projects = []
        self._versions = []
        self._selected_project = None
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        if self.project_type == "modpack":
            self.instance_name_input.clear()
        self.results_table.setRowCount(0)
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.retranslate_dynamic()

    def set_search_result(self, result: ModrinthSearchResult) -> None:
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.offset
        self.results_table.setRowCount(len(self._projects))
        headers = [tr("modrinth.column.name"), tr("modrinth.column.author"), tr("modrinth.column.downloads"), tr("modrinth.column.updated"), tr("modrinth.column.description")]
        self.results_table.setHorizontalHeaderLabels(headers)

        for row, project in enumerate(self._projects):
            values = [project.title, project.author or tr("common.unknown"), f"{project.downloads:,}", project.date_modified[:10], project.description]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, project)
                self.results_table.setItem(row, column, item)

        start = result.offset + 1 if result.projects else 0
        end = result.offset + len(result.projects)
        self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=result.total_hits))
        self.previous_button.setEnabled(result.offset > 0)
        self.next_button.setEnabled(result.offset + result.limit < result.total_hits)
        if self._projects:
            self.results_table.selectRow(0)
        else:
            self._selected_project = None
            self.version_combo.clear()
            self.install_button.setEnabled(False)
            self.details_label.setText(tr("modrinth.results.empty"))

    def set_versions(self, project_id: str, versions: list[ModrinthVersion]) -> None:
        if self._selected_project is None or self._selected_project.project_id != project_id:
            return
        self._versions = list(versions)
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            game_text = ", ".join(version.game_versions[:3])
            if len(version.game_versions) > 3:
                game_text += ", …"
            label = f"{version.version_number} • {version.version_type} • Minecraft {game_text}"
            self.version_combo.addItem(label, version.version_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(bool(self._versions))
        self._version_selected()

    def set_busy(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy)
        self.results_table.setEnabled(not busy)
        self.version_combo.setEnabled(not busy)
        self.install_button.setEnabled(not busy and bool(self._versions))
        self.previous_button.setEnabled(not busy and self._result is not None and self._result.offset > 0)
        self.next_button.setEnabled(not busy and self._result is not None and self._result.offset + self._result.limit < self._result.total_hits)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _request_search(self) -> None:
        if self.project_type == "mod" and self._instance is None:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.mod.no_instance"))
            return
        self._offset = 0
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset)

    def _project_selected(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.results_table.item(rows[0].row(), 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not isinstance(project, ModrinthProject):
            return
        self._selected_project = project
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        if self.project_type == "modpack" and (not self._instance_name_customized or not self.instance_name_input.text().strip() or self.instance_name_input.text() == self._suggested_instance_name):
            self._suggested_instance_name = InstanceManager.next_available_name(self._safe_instance_name(project.title))
            self.instance_name_input.setText(self._suggested_instance_name)
            self._instance_name_customized = False
        game_version = self._instance.version_id if self.project_type == "mod" and self._instance is not None else ""
        self.details_label.setText(tr("modrinth.project.loading_versions", title=project.title))
        self.versions_requested.emit(self.project_type, project.project_id, game_version)

    def _version_selected(self) -> None:
        version = self._selected_version()
        project = self._selected_project
        if version is None or project is None:
            return
        self.details_label.setText(tr("modrinth.project.details", title=project.title, author=project.author or tr("common.unknown"), version=version.version_number, release_type=version.version_type, downloads=f"{project.downloads:,}", description=project.description))

    def _instance_name_edited(self, text: str) -> None:
        self._instance_name_customized = bool(text.strip()) and text != self._suggested_instance_name

    def _request_install(self) -> None:
        version = self._selected_version()
        project = self._selected_project
        if version is None or project is None:
            return
        if self.project_type == "mod":
            self.install_mod_requested.emit(version.version_id)
            return
        name = self.instance_name_input.text().strip()
        self.install_modpack_requested.emit(project.project_id, version.version_id, name, self.optional_checkbox.isChecked())

    def _selected_version(self) -> ModrinthVersion | None:
        index = self.version_combo.currentIndex()
        if index < 0 or index >= len(self._versions):
            return None
        version_id = str(self.version_combo.currentData() or "")
        return next((version for version in self._versions if version.version_id == version_id), None)

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self.PAGE_SIZE)
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset)

    def _next_page(self) -> None:
        self._offset += self.PAGE_SIZE
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset)

    @staticmethod
    def _safe_instance_name(value: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", str(value)).strip().rstrip(". ")
        return cleaned[:80] or "Modrinth Modpack"

    def retranslate_dynamic(self) -> None:
        is_mod = self.project_type == "mod"
        self.setWindowTitle(tr("modrinth.mod.title" if is_mod else "modrinth.modpack.title"))
        self.title_label.setText(tr("modrinth.mod.title" if is_mod else "modrinth.modpack.title"))
        if is_mod:
            if self._instance is None:
                self.context_label.setText(tr("modrinth.mod.context.none"))
            else:
                self.context_label.setText(tr("modrinth.mod.context", instance=self._instance.name, minecraft=self._instance.version_id))
        else:
            self.context_label.setText(tr("modrinth.modpack.context"))
        self.search_input.setPlaceholderText(tr("modrinth.search.placeholder"))
        self.search_button.setText(tr("common.search"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.install_button.setText(tr("modrinth.mod.install" if is_mod else "modrinth.modpack.install"))
        self.instance_name_input.setPlaceholderText(tr("modrinth.modpack.instance_name"))
        self.optional_checkbox.setText(tr("modrinth.modpack.optional_files"))
        self.sort_combo.setItemText(0, tr("modrinth.sort.relevance"))
        self.sort_combo.setItemText(1, tr("modrinth.sort.downloads"))
        self.sort_combo.setItemText(2, tr("modrinth.sort.updated"))
        self.sort_combo.setItemText(3, tr("modrinth.sort.newest"))
        if self._result is None:
            self.result_count_label.setText(tr("modrinth.results.ready"))
        else:
            start = self._result.offset + 1 if self._result.projects else 0
            end = self._result.offset + len(self._result.projects)
            self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=self._result.total_hits))
        self.results_table.setHorizontalHeaderLabels([tr("modrinth.column.name"), tr("modrinth.column.author"), tr("modrinth.column.downloads"), tr("modrinth.column.updated"), tr("modrinth.column.description")])
