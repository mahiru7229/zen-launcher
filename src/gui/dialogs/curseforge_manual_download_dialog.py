from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from src.core.language.language_manager import tr
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.curseforge.manual_download import CurseForgeManualDownload


class CurseForgeManualDownloadDialog(QDialog):
    file_selected = Signal(object, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._requirements: list[CurseForgeManualDownload] = []
        self._installed: set[tuple[int, int]] = set()
        resize_dialog_to_screen(self, 820, 480, 640, 380)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.summary_label)

        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.open_page_button = QPushButton()
        self.select_file_button = QPushButton()
        self.close_button = QPushButton()
        self.open_page_button.clicked.connect(self._open_page)
        self.select_file_button.clicked.connect(self._select_file)
        self.close_button.clicked.connect(self.accept)
        actions.addWidget(self.open_page_button)
        actions.addWidget(self.select_file_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        self.retranslate_dynamic()

    def set_requirements(self, requirements: tuple[CurseForgeManualDownload, ...] | list[CurseForgeManualDownload]) -> None:
        self._requirements = list(requirements)
        self._installed.clear()
        self._render()

    def mark_installed(self, requirement: CurseForgeManualDownload) -> None:
        self._installed.add((requirement.project_id, requirement.file_id))
        self._render()

    def _render(self) -> None:
        self.table.setRowCount(len(self._requirements))
        for row, requirement in enumerate(self._requirements):
            installed = (requirement.project_id, requirement.file_id) in self._installed
            values = [
                requirement.project_name,
                requirement.file_name,
                f"{requirement.file_size / (1024 * 1024):.1f} MB" if requirement.file_size > 0 else "—",
                tr("curseforge.manual.status.installed") if installed else tr("curseforge.manual.status.waiting"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, requirement)
                self.table.setItem(row, column, item)
        if self._requirements and self.table.currentRow() < 0:
            self.table.selectRow(0)
        remaining = len(self._requirements) - len(self._installed)
        self.summary_label.setText(tr("curseforge.manual.summary", count=remaining))
        self.select_file_button.setEnabled(remaining > 0)

    def _selected_requirement(self) -> CurseForgeManualDownload | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        requirement = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        return requirement if isinstance(requirement, CurseForgeManualDownload) else None

    def _open_page(self) -> None:
        requirement = self._selected_requirement()
        if requirement is not None and requirement.project_url:
            QDesktopServices.openUrl(QUrl(requirement.project_url))

    def _select_file(self) -> None:
        requirement = self._selected_requirement()
        if requirement is None:
            return
        selected, _ = QFileDialog.getOpenFileName(
            self,
            tr("curseforge.manual.select_title"),
            str(Path.home() / "Downloads"),
            tr("curseforge.manual.file_filter"),
        )
        if selected:
            self.file_selected.emit(requirement, Path(selected))

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("curseforge.manual.title"))
        self.title_label.setText(tr("curseforge.manual.title"))
        self.table.setHorizontalHeaderLabels([
            tr("curseforge.column.name"),
            tr("curseforge.manual.column.file"),
            tr("curseforge.manual.column.size"),
            tr("curseforge.manual.column.status"),
        ])
        self.open_page_button.setText(tr("curseforge.manual.open_page"))
        self.select_file_button.setText(tr("curseforge.manual.select_file"))
        self.close_button.setText(tr("common.close"))
        self._render()
