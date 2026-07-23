from __future__ import annotations

from datetime import datetime, timezone
import re

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.instance.instance_manager import InstanceManager
from src.core.language.language_manager import tr
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.gui.theme.runtime import set_theme_icon
from src.gui.window_sizing import resize_dialog_to_screen
from src.models.curseforge.cache import CurseForgeCacheInfo
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult
from src.models.instance.instance import Instance


class CurseForgeBrowserDialog(QDialog):
    search_requested = Signal(str, str, str, int)
    refresh_requested = Signal(str, str, str, int)
    files_requested = Signal(str, int, str, str, object)
    files_refresh_requested = Signal(str, int, str, str, object)
    clear_cache_requested = Signal()
    install_mod_requested = Signal(int, int, object)
    install_modpack_requested = Signal(int, int, str, bool, object)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self, project_type: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CurseForgeDialog")
        self.project_type = project_type
        self._instance: Instance | None = None
        self._catalog_loader = ""
        self._result: CurseForgeSearchResult | None = None
        self._projects: list[CurseForgeProject] = []
        self._files: list[CurseForgeFile] = []
        self._selected_project: CurseForgeProject | None = None
        self._index = 0
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        self._pending_channel_preferences = (False, False)
        self._cache_info = CurseForgeClient.cache_status()
        self._refresh_files_after_search = False
        self._channel_change_timer = QTimer(self)
        self._channel_change_timer.setSingleShot(True)
        self._channel_change_timer.setInterval(25)
        self._channel_change_timer.timeout.connect(self._apply_queued_channel_change)
        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.setInterval(1000)
        self._cooldown_timer.timeout.connect(self._render_cache_status)
        self._cooldown_timer.start()
        self._build_ui()
        self.retranslate_dynamic()
        self.set_cache_info(self._cache_info)

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 1120, 720, 900, 560)
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
        self.sort_combo.addItem("Popularity", "popularity")
        self.sort_combo.addItem("Downloads", "downloads")
        self.sort_combo.addItem("Recently updated", "updated")
        self.sort_combo.addItem("Newest", "newest")
        self.search_button = set_theme_icon(QPushButton(), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        provider_row = QHBoxLayout()
        self.cache_status_label = QLabel()
        self.cache_status_label.setObjectName("MutedLabel")
        self.cache_status_label.setWordWrap(True)
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.refresh_button.clicked.connect(self._request_refresh)
        self.clear_cache_button = QPushButton()
        self.clear_cache_button.clicked.connect(self.clear_cache_requested.emit)
        provider_row.addWidget(self.cache_status_label, 1)
        provider_row.addWidget(self.refresh_button)
        provider_row.addWidget(self.clear_cache_button)
        root.addLayout(provider_row)

        channel_row = QHBoxLayout()
        self.release_channel_label = QLabel()
        self.release_channel_label.setObjectName("MutedLabel")
        self.include_beta_checkbox = QCheckBox()
        self.include_alpha_checkbox = QCheckBox()
        self.include_beta_checkbox.toggled.connect(self._channels_changed)
        self.include_alpha_checkbox.toggled.connect(self._channels_changed)
        channel_row.addWidget(self.release_channel_label)
        channel_row.addStretch()
        channel_row.addWidget(self.include_beta_checkbox)
        channel_row.addWidget(self.include_alpha_checkbox)
        root.addLayout(channel_row)

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
        self.previous_button = set_theme_icon(QPushButton(), "icon.action.previous")
        self.next_button = set_theme_icon(QPushButton(), "icon.action.next")
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        page_row.addWidget(self.result_count_label)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        root.addLayout(page_row)

        selection_row = QHBoxLayout()
        self.file_combo = QComboBox()
        self.file_combo.currentIndexChanged.connect(self._file_selected)
        self.instance_name_input = QLineEdit()
        self.instance_name_input.textEdited.connect(self._instance_name_edited)
        self.optional_checkbox = QCheckBox()
        self.optional_checkbox.setChecked(True)
        self.install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        selection_row.addWidget(self.file_combo, 2)
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

    @property
    def loader(self) -> str:
        if self.project_type == "modpack":
            return ModLoaderManager.FORGE
        if self._instance is not None:
            return ModLoaderManager.normalize(self._instance.mod_loader)[0]
        return self._catalog_loader

    @property
    def catalog_mode(self) -> bool:
        return self.project_type == "mod" and self._instance is None and bool(self._catalog_loader)

    @property
    def allowed_release_types(self) -> tuple[str, ...]:
        values = ["release"]
        if self.include_beta_checkbox.isChecked():
            values.append("beta")
        if self.include_alpha_checkbox.isChecked():
            values.append("alpha")
        return tuple(values)

    def set_channel_preferences(self, include_beta: bool, include_alpha: bool) -> None:
        self.include_beta_checkbox.blockSignals(True)
        self.include_alpha_checkbox.blockSignals(True)
        self.include_beta_checkbox.setChecked(bool(include_beta))
        self.include_alpha_checkbox.setChecked(bool(include_alpha))
        self.include_beta_checkbox.blockSignals(False)
        self.include_alpha_checkbox.blockSignals(False)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._catalog_loader = ""
        self._index = 0
        self._result = None
        self._projects = []
        self._files = []
        self._selected_project = None
        self._suggested_instance_name = ""
        self._instance_name_customized = False
        self.results_table.setRowCount(0)
        self.file_combo.clear()
        self.install_button.setEnabled(False)
        if self.project_type == "modpack":
            self.instance_name_input.clear()
        self.retranslate_dynamic()


    def set_catalog_loader(self, loader: str) -> None:
        normalized = CurseForgeClient.normalize_loader(loader)
        if normalized not in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE}:
            raise RuntimeError(f"Unsupported CurseForge loader: {loader or 'unknown'}")
        self.set_instance(None)
        self._catalog_loader = normalized
        self.retranslate_dynamic()

    def set_search_result(self, result: CurseForgeSearchResult) -> None:
        self._result = result
        self._projects = list(result.projects)
        self._index = result.index
        self.set_cache_info(result.cache_info)
        self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            for row, project in enumerate(self._projects):
                values = [project.name, ", ".join(project.authors) or tr("common.unknown"), f"{project.download_count:,}", project.date_modified[:10], project.summary]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, project)
                    self.results_table.setItem(row, column, item)
            if self._projects:
                self.results_table.selectRow(0)
        finally:
            self.results_table.blockSignals(False)
        start = result.index + 1 if result.projects else 0
        end = result.index + len(result.projects)
        self.result_count_label.setText(tr("curseforge.results.range", start=start, end=end, total=result.total_count))
        self.previous_button.setEnabled(result.index > 0)
        self.next_button.setEnabled(result.index + result.page_size < result.total_count)
        if self._projects:
            self._select_project(self._projects[0])
        else:
            self._clear_selection(tr("curseforge.results.empty"))

    def set_files(self, project_id: int, files: list[CurseForgeFile]) -> None:
        if self._selected_project is None or self._selected_project.project_id != int(project_id):
            return
        self._files = list(files)
        self.file_combo.blockSignals(True)
        self.file_combo.clear()
        for file in self._files:
            games = ", ".join(file.game_versions[:3])
            self.file_combo.addItem(f"{file.display_name} • {file.release_type} • {games}", file.file_id)
        self.file_combo.blockSignals(False)
        self.install_button.setEnabled(bool(self._files))
        if self._files:
            self._file_selected()
        else:
            channels = ", ".join(value.title() for value in self.allowed_release_types)
            self.details_label.setText(
                tr(
                    "curseforge.files.none_for_loader",
                    loader=self.loader.title(),
                    channels=channels,
                )
            )

    def set_cache_info(self, info: CurseForgeCacheInfo) -> None:
        if isinstance(info, CurseForgeCacheInfo):
            self._cache_info = info
        self._render_cache_status()

    def set_busy(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy)
        self.results_table.setEnabled(not busy)
        self.file_combo.setEnabled(not busy)
        self.include_beta_checkbox.setEnabled(not busy)
        self.include_alpha_checkbox.setEnabled(not busy)
        self.clear_cache_button.setEnabled(not busy)
        self.install_button.setEnabled(not busy and bool(self._files))
        self.previous_button.setEnabled(not busy and self._result is not None and self._result.index > 0)
        self.next_button.setEnabled(not busy and self._result is not None and self._result.index + self._result.page_size < self._result.total_count)
        self._render_cache_status()

    def _channels_changed(self, _checked: bool) -> None:
        self._pending_channel_preferences = (
            self.include_beta_checkbox.isChecked(),
            self.include_alpha_checkbox.isChecked(),
        )
        self._channel_change_timer.start()

    def _apply_queued_channel_change(self) -> None:
        include_beta, include_alpha = self._pending_channel_preferences
        self.channel_preferences_changed.emit(include_beta, include_alpha)
        if self._selected_project is not None:
            self.files_requested.emit(self.project_type, self._selected_project.project_id, self.game_version, self.loader, self.allowed_release_types)

    def _request_search(self) -> None:
        if self.project_type == "mod" and self._instance is None and not self._catalog_loader:
            QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.mod.no_instance"))
            return
        if not self.search_input.text().strip():
            QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.search.required"))
            return
        self._index = 0
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._index)

    def _request_refresh(self) -> None:
        if not self.search_input.text().strip():
            QMessageBox.information(self, tr("curseforge.title"), tr("curseforge.search.required"))
            return
        if CurseForgeClient.manual_refresh_remaining_seconds() > 0:
            self._render_cache_status()
            return
        self._refresh_files_after_search = True
        self.refresh_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._index)

    def _project_selected(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.results_table.item(rows[0].row(), 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, CurseForgeProject):
            self._select_project(project)

    def _select_project(self, project: CurseForgeProject) -> None:
        self._selected_project = project
        self._files = []
        self.file_combo.clear()
        self.install_button.setEnabled(False)
        if self.project_type == "modpack" and (not self._instance_name_customized or not self.instance_name_input.text().strip() or self.instance_name_input.text() == self._suggested_instance_name):
            self._suggested_instance_name = InstanceManager.next_available_name(self._safe_instance_name(project.name))
            self.instance_name_input.setText(self._suggested_instance_name)
            self._instance_name_customized = False
        self.details_label.setText(tr("curseforge.project.loading_files", name=project.name))
        if self._refresh_files_after_search:
            self._refresh_files_after_search = False
            self.files_refresh_requested.emit(self.project_type, project.project_id, self.game_version, self.loader, self.allowed_release_types)
        else:
            self.files_requested.emit(self.project_type, project.project_id, self.game_version, self.loader, self.allowed_release_types)

    def _clear_selection(self, message: str) -> None:
        self._selected_project = None
        self._files = []
        self.file_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(message)

    def _file_selected(self) -> None:
        file = self.selected_file()
        project = self._selected_project
        if file is None or project is None:
            return
        distribution = tr("curseforge.file.manual_required") if not file.download_url or not file.is_available else tr("curseforge.file.automatic")
        self.details_label.setText(tr("curseforge.project.details", name=project.name, authors=", ".join(project.authors) or tr("common.unknown"), version=file.display_name, release_type=file.release_type, downloads=f"{project.download_count:,}", description=f"{project.summary}\n{distribution}"))

    def _instance_name_edited(self, text: str) -> None:
        self._instance_name_customized = bool(text.strip()) and text != self._suggested_instance_name

    def _request_install(self) -> None:
        file = self.selected_file()
        project = self._selected_project
        if file is None or project is None:
            return
        if self.project_type == "mod":
            self.install_mod_requested.emit(project.project_id, file.file_id, self.allowed_release_types)
            return
        self.install_modpack_requested.emit(project.project_id, file.file_id, self.instance_name_input.text().strip(), self.optional_checkbox.isChecked(), self.allowed_release_types)

    def selected_file(self) -> CurseForgeFile | None:
        file_id = int(self.file_combo.currentData() or 0)
        return next((file for file in self._files if file.file_id == file_id), None)

    def _previous_page(self) -> None:
        self._index = max(0, self._index - self.PAGE_SIZE)
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._index)

    def _next_page(self) -> None:
        self._index += self.PAGE_SIZE
        self.search_requested.emit(self.project_type, self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._index)

    def _render_cache_status(self) -> None:
        info = self._cache_info
        age = self._format_age(info.refreshed_at)
        size_mb = info.cache_size_bytes / (1024 * 1024)
        limit_mb = info.cache_limit_bytes / (1024 * 1024)
        source = tr("curseforge.cache.source.stale") if info.stale else tr("curseforge.cache.source.cached") if info.from_cache else tr("curseforge.cache.source.live")
        if not info.refreshed_at:
            text = tr("curseforge.cache.never", size=f"{size_mb:.1f}", limit=f"{limit_mb:.0f}")
        else:
            text = tr("curseforge.cache.status", age=age, source=source, size=f"{size_mb:.1f}", limit=f"{limit_mb:.0f}")
        if info.last_error:
            text += " · " + tr("curseforge.cache.last_error")
        self.cache_status_label.setText(text)
        remaining = CurseForgeClient.manual_refresh_remaining_seconds()
        self.refresh_button.setEnabled(remaining <= 0 and self.search_button.isEnabled())
        self.refresh_button.setText(tr("curseforge.cache.refresh_wait", seconds=remaining) if remaining > 0 else tr("curseforge.cache.refresh"))

    @staticmethod
    def _format_age(value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            return tr("curseforge.cache.never_value")
        try:
            refreshed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return normalized
        if refreshed.tzinfo is None:
            refreshed = refreshed.replace(tzinfo=timezone.utc)
        seconds = max(0, int((datetime.now(timezone.utc) - refreshed).total_seconds()))
        if seconds < 10:
            return tr("curseforge.cache.just_now")
        if seconds < 60:
            return tr("curseforge.cache.seconds_ago", value=seconds)
        minutes = seconds // 60
        if minutes < 60:
            return tr("curseforge.cache.minutes_ago", value=minutes)
        hours = minutes // 60
        if hours < 24:
            return tr("curseforge.cache.hours_ago", value=hours)
        return tr("curseforge.cache.days_ago", value=hours // 24)

    @staticmethod
    def _safe_instance_name(value: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", str(value)).strip().rstrip(". ")
        return cleaned[:80] or "CurseForge Modpack"

    def retranslate_dynamic(self) -> None:
        is_mod = self.project_type == "mod"
        title = tr("curseforge.mod.title" if is_mod else "curseforge.modpack.title")
        self.setWindowTitle(title)
        self.title_label.setText(title)
        if is_mod:
            if self._instance is not None:
                self.context_label.setText(tr("curseforge.mod.context", instance=self._instance.name, minecraft=self._instance.version_id))
            elif self._catalog_loader:
                self.context_label.setText(tr("curseforge.mod.catalog_context", loader=self._catalog_loader.title()))
            else:
                self.context_label.setText(tr("curseforge.mod.context.none"))
        else:
            self.context_label.setText(tr("curseforge.modpack.context"))
        self.release_channel_label.setText(tr("curseforge.channel.release_always"))
        self.include_beta_checkbox.setText(tr("curseforge.channel.beta"))
        self.include_alpha_checkbox.setText(tr("curseforge.channel.alpha"))
        self.search_input.setPlaceholderText(tr("curseforge.search.placeholder"))
        self.search_button.setText(tr("common.search"))
        self.clear_cache_button.setText(tr("curseforge.cache.clear"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.install_button.setText(tr("curseforge.mod.install" if is_mod else "curseforge.modpack.install"))
        self.instance_name_input.setPlaceholderText(tr("curseforge.modpack.instance_name"))
        self.optional_checkbox.setText(tr("curseforge.modpack.optional_files"))
        self.sort_combo.setItemText(0, tr("curseforge.sort.popularity"))
        self.sort_combo.setItemText(1, tr("curseforge.sort.downloads"))
        self.sort_combo.setItemText(2, tr("curseforge.sort.updated"))
        self.sort_combo.setItemText(3, tr("curseforge.sort.newest"))
        self.results_table.setHorizontalHeaderLabels([tr("curseforge.column.name"), tr("curseforge.column.author"), tr("curseforge.column.downloads"), tr("curseforge.column.updated"), tr("curseforge.column.description")])
        if self._result is None:
            self.result_count_label.setText(tr("curseforge.results.ready"))
        self._render_cache_status()
