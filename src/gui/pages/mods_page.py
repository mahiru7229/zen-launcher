from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.language.language_manager import tr
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.gui.pages.base_page import BasePage
from src.gui.theme.runtime import set_theme_icon
from src.gui.widget.card_widget import CardWidget
from src.models.curseforge.cache import CurseForgeCacheInfo
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthVersion


class ModsPage(BasePage):
    search_requested = Signal(str, str, int, str)
    versions_requested = Signal(str, str)
    install_requested = Signal(object, str, object)
    curseforge_search_requested = Signal(str, str, int, str)
    curseforge_refresh_requested = Signal(str, str, int, str)
    curseforge_files_requested = Signal(int, str, object)
    curseforge_files_refresh_requested = Signal(int, str, object)
    curseforge_clear_cache_requested = Signal()
    curseforge_install_requested = Signal(object, str, object)
    channel_preferences_changed = Signal(bool, bool)

    PAGE_SIZE = 25

    def __init__(self) -> None:
        super().__init__(tr("mods.title"), tr("mods.subtitle"), "mods")
        self._result: ModrinthSearchResult | CurseForgeSearchResult | None = None
        self._projects: list[ModrinthProject | CurseForgeProject] = []
        self._all_versions: list[ModrinthVersion] = []
        self._versions: list[ModrinthVersion] = []
        self._curseforge_files: list[CurseForgeFile] = []
        self._selected_project: ModrinthProject | CurseForgeProject | None = None
        self._offset = 0
        self._busy = False
        self._refresh_files_after_search = False
        self._pending_channel_preferences = (False, False)
        self._cache_info = CurseForgeClient.cache_status()

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
        self.set_curseforge_cache_info(self._cache_info)

    def _build_ui(self) -> None:
        selector_card = CardWidget(tr("mods.catalog.selector.title"), tr("mods.catalog.selector.subtitle"))
        selector_grid = QGridLayout()
        selector_grid.setHorizontalSpacing(12)
        selector_grid.setVerticalSpacing(10)
        selector_grid.setColumnStretch(1, 1)

        self.provider_label = QLabel()
        self.provider_label.setObjectName("MutedLabel")
        self.provider_combo = QComboBox()
        self.provider_combo.addItem(tr("mods.catalog.provider.modrinth"), "modrinth")
        self.provider_combo.addItem(tr("mods.catalog.provider.curseforge"), "curseforge")
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)

        self.loader_label = QLabel()
        self.loader_label.setObjectName("MutedLabel")
        self.loader_combo = QComboBox()
        self.loader_combo.addItem("Fabric", ModLoaderManager.FABRIC)
        self.loader_combo.addItem("Forge", ModLoaderManager.FORGE)
        self.loader_combo.currentIndexChanged.connect(self._loader_changed)

        selector_grid.addWidget(self.provider_label, 0, 0)
        selector_grid.addWidget(self.provider_combo, 0, 1)
        selector_grid.addWidget(self.loader_label, 1, 0)
        selector_grid.addWidget(self.loader_combo, 1, 1)
        selector_card.layout.addLayout(selector_grid)

        browser_card = CardWidget("")
        self.browser_card = browser_card
        self.catalog_title_label = QLabel()
        self.catalog_title_label.setObjectName("CardTitle")
        self.catalog_subtitle_label = QLabel()
        self.catalog_subtitle_label.setObjectName("CardSubtitle")
        self.catalog_subtitle_label.setWordWrap(True)
        browser_card.layout.addWidget(self.catalog_title_label)
        browser_card.layout.addWidget(self.catalog_subtitle_label)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self._request_search)

        self.sort_combo = QComboBox()

        self.search_button = set_theme_icon(QPushButton(tr("common.search")), "icon.action.search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(self._request_search)

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.sort_combo)
        search_row.addWidget(self.search_button)
        browser_card.layout.addLayout(search_row)

        cache_row = QHBoxLayout()
        self.cache_status_label = QLabel()
        self.cache_status_label.setObjectName("MutedLabel")
        self.cache_status_label.setWordWrap(True)
        self.refresh_button = set_theme_icon(QPushButton(), "icon.action.refresh")
        self.refresh_button.clicked.connect(self._request_refresh)
        self.clear_cache_button = QPushButton()
        self.clear_cache_button.clicked.connect(self.curseforge_clear_cache_requested.emit)
        cache_row.addWidget(self.cache_status_label, 1)
        cache_row.addWidget(self.refresh_button)
        cache_row.addWidget(self.clear_cache_button)
        browser_card.layout.addLayout(cache_row)

        channel_row = QHBoxLayout()
        self.release_channel_label = QLabel()
        self.release_channel_label.setObjectName("MutedLabel")
        self.release_channel_label.setWordWrap(True)
        self.include_beta_checkbox = QCheckBox()
        self.include_alpha_checkbox = QCheckBox()
        self.include_beta_checkbox.toggled.connect(self._channels_changed)
        self.include_alpha_checkbox.toggled.connect(self._channels_changed)
        channel_row.addWidget(self.release_channel_label, 1)
        channel_row.addWidget(self.include_beta_checkbox)
        channel_row.addWidget(self.include_alpha_checkbox)
        browser_card.layout.addLayout(channel_row)

        self.results_table = QTableWidget(0, 5)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.results_table.itemSelectionChanged.connect(self._project_selected)
        self.results_table.setMinimumHeight(260)
        browser_card.layout.addWidget(self.results_table, 1)

        page_row = QHBoxLayout()
        self.result_count_label = QLabel()
        self.result_count_label.setObjectName("MutedLabel")
        self.previous_button = set_theme_icon(QPushButton(), "icon.action.previous")
        self.next_button = set_theme_icon(QPushButton(), "icon.action.next")
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        page_row.addWidget(self.result_count_label)
        page_row.addStretch()
        page_row.addWidget(self.previous_button)
        page_row.addWidget(self.next_button)
        browser_card.layout.addLayout(page_row)

        install_row = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._version_selected)
        self.install_button = set_theme_icon(QPushButton(), "icon.action.download")
        self.install_button.setObjectName("PrimaryButton")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self._request_install)
        install_row.addWidget(self.version_combo, 1)
        install_row.addWidget(self.install_button)
        browser_card.layout.addLayout(install_row)

        self.details_label = QLabel()
        self.details_label.setObjectName("MutedLabel")
        self.details_label.setWordWrap(True)
        self.details_label.setMinimumHeight(70)
        browser_card.layout.addWidget(self.details_label)

        self.root_layout.addWidget(selector_card)
        self.root_layout.addWidget(browser_card)
        self.root_layout.addStretch()

    @property
    def has_loaded_search(self) -> bool:
        return self._result is not None or bool(self._projects)

    @property
    def selected_provider(self) -> str:
        provider = str(self.provider_combo.currentData() or "modrinth").strip().lower()
        return provider if provider in {"modrinth", "curseforge"} else "modrinth"

    @property
    def selected_loader(self) -> str:
        loader = str(self.loader_combo.currentData() or ModLoaderManager.FABRIC).strip().lower()
        return loader if loader in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE} else ModLoaderManager.FABRIC

    @property
    def allowed_version_types(self) -> tuple[str, ...]:
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
        if self.selected_provider == "modrinth":
            self._apply_modrinth_version_filter()

    def set_searching(self, loader: str = "", provider: str = "modrinth") -> None:
        if str(provider).strip().lower() != self.selected_provider:
            return
        if loader and str(loader).strip().lower() != self.selected_loader:
            return
        self._clear_search_state()
        if self.selected_provider == "curseforge":
            self.result_count_label.setText(tr("mods.catalog.curseforge.searching"))
            self._clear_project_selection(tr("mods.catalog.curseforge.contacting"))
        else:
            self.result_count_label.setText(tr("modrinth.results.searching"))
            self._clear_project_selection(tr("modrinth.results.contacting"))

    def set_search_error(self, loader: str, message: str) -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._clear_search_state()
        self.result_count_label.setText(tr("modrinth.results.failed"))
        self._clear_project_selection(tr("modrinth.results.error", error=str(message)))

    def set_curseforge_search_error(self, loader: str, message: str) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._clear_search_state()
        self.result_count_label.setText(tr("mods.catalog.curseforge.failed"))
        self._clear_project_selection(tr("mods.catalog.curseforge.error", error=str(message)))

    def set_curseforge_files_error(self, project_id: int, loader: str, message: str) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, CurseForgeProject) or self._selected_project.project_id != int(project_id):
            return
        self._curseforge_files = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(tr("mods.catalog.version_error", error=str(message)))

    def set_search_result(self, result: ModrinthSearchResult, loader: str = "") -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.offset
        self._render_project_rows()
        start = result.offset + 1 if result.projects else 0
        end = result.offset + len(result.projects)
        self.result_count_label.setText(tr("modrinth.results.range", start=start, end=end, total=result.total_hits))
        self.previous_button.setEnabled(not self._busy and result.offset > 0)
        self.next_button.setEnabled(not self._busy and result.offset + result.limit < result.total_hits)
        self._select_first_project_or_show_empty(tr("modrinth.results.empty"))

    def set_curseforge_search_result(self, loader: str, result: CurseForgeSearchResult) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        self._result = result
        self._projects = list(result.projects)
        self._offset = result.index
        self.set_curseforge_cache_info(result.cache_info)
        self._render_project_rows()
        start = result.index + 1 if result.projects else 0
        end = result.index + len(result.projects)
        self.result_count_label.setText(tr("curseforge.results.range", start=start, end=end, total=result.total_count))
        self.previous_button.setEnabled(not self._busy and result.index > 0)
        self.next_button.setEnabled(not self._busy and result.index + result.page_size < result.total_count)
        self._select_first_project_or_show_empty(tr("curseforge.results.empty"))

    def set_versions(self, project_id: str, versions: list[ModrinthVersion], loader: str = "") -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, ModrinthProject) or self._selected_project.project_id != project_id:
            return
        self._all_versions = list(versions)
        self._apply_modrinth_version_filter()

    def set_versions_error(self, project_id: str, loader: str, message: str) -> None:
        if self.selected_provider != "modrinth" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, ModrinthProject) or self._selected_project.project_id != project_id:
            return
        self._all_versions = []
        self._versions = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(tr("mods.catalog.version_error", error=str(message)))

    def set_curseforge_files(self, project_id: int, loader: str, files: list[CurseForgeFile]) -> None:
        if self.selected_provider != "curseforge" or (loader and str(loader).strip().lower() != self.selected_loader):
            return
        if not isinstance(self._selected_project, CurseForgeProject) or self._selected_project.project_id != int(project_id):
            return
        self._curseforge_files = list(files)
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for file in self._curseforge_files:
            games = ", ".join(file.game_versions[:4])
            if len(file.game_versions) > 4:
                games += ", …"
            self.version_combo.addItem(f"{file.display_name} • {file.release_type} • Minecraft {games}", file.file_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(not self._busy and bool(self._curseforge_files))
        self._update_channel_summary()
        if self._curseforge_files:
            self._version_selected()
        else:
            channels = ", ".join(value.title() for value in self.allowed_version_types)
            self.details_label.setText(tr("curseforge.files.none_for_loader", loader=self.selected_loader.title(), channels=channels))

    def set_curseforge_cache_info(self, info: CurseForgeCacheInfo) -> None:
        if isinstance(info, CurseForgeCacheInfo):
            self._cache_info = info
        self._render_cache_status()

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self.provider_combo.setEnabled(not self._busy)
        self.loader_combo.setEnabled(not self._busy)
        self.search_input.setEnabled(not self._busy)
        self.search_button.setEnabled(not self._busy)
        self.results_table.setEnabled(not self._busy)
        self.version_combo.setEnabled(not self._busy)
        self.sort_combo.setEnabled(not self._busy)
        self.include_beta_checkbox.setEnabled(not self._busy)
        self.include_alpha_checkbox.setEnabled(not self._busy)
        self.clear_cache_button.setEnabled(not self._busy)
        self.install_button.setEnabled(not self._busy and self._has_installable_items())
        self._update_pagination_buttons()
        self._render_cache_status()

    def start_search(self) -> None:
        if self.selected_provider == "modrinth":
            self._request_search()

    def _request_search(self) -> None:
        self._offset = 0
        if self.selected_provider == "curseforge":
            if not self.search_input.text().strip():
                self.result_count_label.setText(tr("curseforge.results.ready"))
                self._clear_project_selection(tr("curseforge.search.required"))
                return
            self._refresh_files_after_search = False
            self.set_searching(self.selected_loader, "curseforge")
            self.curseforge_search_requested.emit(self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._offset, self.selected_loader)
            return
        self.set_searching(self.selected_loader, "modrinth")
        self.search_requested.emit(self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)

    def _request_refresh(self) -> None:
        if self.selected_provider != "curseforge":
            return
        if not self.search_input.text().strip():
            self.result_count_label.setText(tr("curseforge.results.ready"))
            self._clear_project_selection(tr("curseforge.search.required"))
            return
        if CurseForgeClient.manual_refresh_remaining_seconds() > 0:
            self._render_cache_status()
            return
        self._refresh_files_after_search = True
        self.set_searching(self.selected_loader, "curseforge")
        self.curseforge_refresh_requested.emit(self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._offset, self.selected_loader)

    def _project_selected(self) -> None:
        rows = self.results_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.results_table.item(rows[0].row(), 0)
        project = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if isinstance(project, (ModrinthProject, CurseForgeProject)):
            self._select_project(project)

    def _select_project(self, project: ModrinthProject | CurseForgeProject) -> None:
        self._selected_project = project
        self._all_versions = []
        self._versions = []
        self._curseforge_files = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        if isinstance(project, CurseForgeProject):
            self.details_label.setText(tr("curseforge.project.loading_files", name=project.name))
            if self._refresh_files_after_search:
                self._refresh_files_after_search = False
                self.curseforge_files_refresh_requested.emit(project.project_id, self.selected_loader, self.allowed_version_types)
            else:
                self.curseforge_files_requested.emit(project.project_id, self.selected_loader, self.allowed_version_types)
            return
        self.details_label.setText(tr("modrinth.project.loading_versions", title=project.title))
        self.versions_requested.emit(project.project_id, self.selected_loader)

    def _clear_project_selection(self, message: str) -> None:
        self._selected_project = None
        self._all_versions = []
        self._versions = []
        self._curseforge_files = []
        self.version_combo.clear()
        self.install_button.setEnabled(False)
        self.details_label.setText(message)

    def _apply_modrinth_version_filter(self) -> None:
        self._update_channel_summary()
        allowed = set(self.allowed_version_types)
        loader = self.selected_loader
        self._versions = [version for version in self._all_versions if version.version_type in allowed and loader in {str(item).strip().lower() for item in version.loaders}]
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        for version in self._versions:
            game_text = ", ".join(version.game_versions[:4])
            if len(version.game_versions) > 4:
                game_text += ", …"
            self.version_combo.addItem(f"{version.version_number} • {version.version_type} • Minecraft {game_text}", version.version_id)
        self.version_combo.blockSignals(False)
        self.install_button.setEnabled(not self._busy and bool(self._versions))
        if self._versions:
            self._version_selected()
        elif isinstance(self._selected_project, ModrinthProject):
            channels = ", ".join(item.title() for item in self.allowed_version_types)
            self.details_label.setText(tr("modrinth.channel.no_versions", channels=channels))

    def _update_channel_summary(self) -> None:
        if self.selected_provider == "curseforge":
            self.release_channel_label.setText(tr("curseforge.channel.release_always"))
            return
        if not self._all_versions:
            self.release_channel_label.setText(tr("modrinth.channel.release_always"))
            return
        counts = {"release": 0, "beta": 0, "alpha": 0}
        for version in self._all_versions:
            if version.version_type in counts:
                counts[version.version_type] += 1
        self.release_channel_label.setText(tr("modrinth.channel.summary", release=counts["release"], beta=counts["beta"], alpha=counts["alpha"]))

    def _version_selected(self) -> None:
        if self.selected_provider == "curseforge":
            file = self.selected_curseforge_file()
            project = self._selected_project
            if file is None or not isinstance(project, CurseForgeProject):
                return
            distribution = tr("curseforge.file.manual_required") if not file.download_url or not file.is_available else tr("curseforge.file.automatic")
            self.details_label.setText(tr("curseforge.project.details", name=project.name, authors=", ".join(project.authors) or tr("common.unknown"), version=file.display_name, release_type=file.release_type, downloads=f"{project.download_count:,}", description=f"{project.summary}\n{distribution}"))
            return
        version = self.selected_version()
        project = self._selected_project
        if version is None or not isinstance(project, ModrinthProject):
            return
        game_versions = ", ".join(version.game_versions[:8])
        if len(version.game_versions) > 8:
            game_versions += ", …"
        self.details_label.setText(tr("mods.catalog.details", title=project.title, author=project.author or tr("common.unknown"), version=version.version_number, release_type=version.version_type, minecraft=game_versions, loader=self.selected_loader.title(), description=project.description))

    def _request_install(self) -> None:
        if self.selected_provider == "curseforge":
            file = self.selected_curseforge_file()
            if file is not None:
                self.curseforge_install_requested.emit(file, self.selected_loader, self.allowed_version_types)
            return
        version = self.selected_version()
        if version is not None:
            self.install_requested.emit(version, self.selected_loader, self.allowed_version_types)

    def selected_version(self) -> ModrinthVersion | None:
        if self.selected_provider != "modrinth":
            return None
        index = self.version_combo.currentIndex()
        if index < 0 or index >= len(self._versions):
            return None
        version_id = str(self.version_combo.currentData() or "")
        return next((version for version in self._versions if version.version_id == version_id), None)

    def selected_curseforge_file(self) -> CurseForgeFile | None:
        if self.selected_provider != "curseforge":
            return None
        file_id = int(self.version_combo.currentData() or 0)
        return next((file for file in self._curseforge_files if file.file_id == file_id), None)

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self.PAGE_SIZE)
        self._request_current_page()

    def _next_page(self) -> None:
        self._offset += self.PAGE_SIZE
        self._request_current_page()

    def _request_current_page(self) -> None:
        if self.selected_provider == "curseforge":
            self.set_searching(self.selected_loader, "curseforge")
            self.curseforge_search_requested.emit(self.search_input.text(), str(self.sort_combo.currentData() or "popularity"), self._offset, self.selected_loader)
            return
        self.set_searching(self.selected_loader, "modrinth")
        self.search_requested.emit(self.search_input.text(), str(self.sort_combo.currentData() or "relevance"), self._offset, self.selected_loader)

    def _provider_changed(self, _index: int) -> None:
        self._reset_catalog()
        self._update_provider_ui()

    def _loader_changed(self, _index: int) -> None:
        self._reset_catalog()
        self._update_provider_ui()

    def _channels_changed(self, _checked: bool) -> None:
        self._pending_channel_preferences = (self.include_beta_checkbox.isChecked(), self.include_alpha_checkbox.isChecked())
        self._channel_change_timer.start()

    def _apply_queued_channel_change(self) -> None:
        include_beta, include_alpha = self._pending_channel_preferences
        self.channel_preferences_changed.emit(include_beta, include_alpha)
        if self.selected_provider == "curseforge" and isinstance(self._selected_project, CurseForgeProject):
            self.curseforge_files_requested.emit(self._selected_project.project_id, self.selected_loader, self.allowed_version_types)
        else:
            self._apply_modrinth_version_filter()

    def _render_project_rows(self) -> None:
        self.results_table.blockSignals(True)
        try:
            self.results_table.clearSelection()
            self.results_table.clearContents()
            self.results_table.setRowCount(len(self._projects))
            for row, project in enumerate(self._projects):
                if isinstance(project, CurseForgeProject):
                    values = [project.name, ", ".join(project.authors) or tr("common.unknown"), f"{project.download_count:,}", project.date_modified[:10], project.summary]
                else:
                    values = [project.title, project.author or tr("common.unknown"), f"{project.downloads:,}", project.date_modified[:10], project.description]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, project)
                    self.results_table.setItem(row, column, item)
            if self._projects:
                self.results_table.selectRow(0)
        finally:
            self.results_table.blockSignals(False)

    def _select_first_project_or_show_empty(self, empty_message: str) -> None:
        if self._projects:
            self._select_project(self._projects[0])
        else:
            self._clear_project_selection(empty_message)

    def _clear_search_state(self) -> None:
        self._result = None
        self._projects = []
        self.results_table.clearSelection()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _reset_catalog(self) -> None:
        self._offset = 0
        self._refresh_files_after_search = False
        self._clear_search_state()
        if self.selected_provider == "curseforge":
            self.result_count_label.setText(tr("curseforge.results.ready"))
            self._clear_project_selection(tr("mods.catalog.curseforge.select_project"))
        else:
            self.result_count_label.setText(tr("modrinth.results.ready"))
            self._clear_project_selection(tr("mods.catalog.select_project"))

    def _configure_sort_combo(self) -> None:
        previous = str(self.sort_combo.currentData() or "")
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        if self.selected_provider == "curseforge":
            options = [
                (tr("curseforge.sort.popularity"), "popularity"),
                (tr("curseforge.sort.downloads"), "downloads"),
                (tr("curseforge.sort.updated"), "updated"),
                (tr("curseforge.sort.newest"), "newest"),
            ]
        else:
            options = [
                (tr("modrinth.sort.relevance"), "relevance"),
                (tr("modrinth.sort.downloads"), "downloads"),
                (tr("modrinth.sort.updated"), "updated"),
                (tr("modrinth.sort.newest"), "newest"),
            ]
        for label, value in options:
            self.sort_combo.addItem(label, value)
        index = self.sort_combo.findData(previous)
        self.sort_combo.setCurrentIndex(index if index >= 0 else 0)
        self.sort_combo.blockSignals(False)

    def _update_provider_ui(self) -> None:
        is_curseforge = self.selected_provider == "curseforge"
        self.catalog_title_label.setText(tr("mods.catalog.title.curseforge" if is_curseforge else "mods.catalog.title.modrinth"))
        self.catalog_subtitle_label.setText(tr("mods.catalog.subtitle.curseforge" if is_curseforge else "mods.catalog.subtitle.modrinth"))
        self.search_input.setPlaceholderText(tr("curseforge.search.placeholder" if is_curseforge else "modrinth.search.placeholder"))
        self.cache_status_label.setVisible(is_curseforge)
        self.refresh_button.setVisible(is_curseforge)
        self.clear_cache_button.setVisible(is_curseforge)
        self._configure_sort_combo()
        self._update_channel_summary()
        self.results_table.setHorizontalHeaderLabels(
            [
                tr("curseforge.column.name" if is_curseforge else "modrinth.column.name"),
                tr("curseforge.column.author" if is_curseforge else "modrinth.column.author"),
                tr("curseforge.column.downloads" if is_curseforge else "modrinth.column.downloads"),
                tr("curseforge.column.updated" if is_curseforge else "modrinth.column.updated"),
                tr("curseforge.column.description" if is_curseforge else "modrinth.column.description"),
            ]
        )
        self._render_cache_status()

    def _update_pagination_buttons(self) -> None:
        if self._busy or self._result is None:
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        if isinstance(self._result, CurseForgeSearchResult):
            self.previous_button.setEnabled(self._result.index > 0)
            self.next_button.setEnabled(self._result.index + self._result.page_size < self._result.total_count)
            return
        self.previous_button.setEnabled(self._result.offset > 0)
        self.next_button.setEnabled(self._result.offset + self._result.limit < self._result.total_hits)

    def _has_installable_items(self) -> bool:
        return bool(self._curseforge_files if self.selected_provider == "curseforge" else self._versions)

    def _render_cache_status(self) -> None:
        if not hasattr(self, "cache_status_label") or self.selected_provider != "curseforge":
            return
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
        self.refresh_button.setEnabled(not self._busy and remaining <= 0)
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

    def retranslate_dynamic(self) -> None:
        self.provider_label.setText(tr("mods.catalog.provider.label"))
        self.provider_combo.setItemText(0, tr("mods.catalog.provider.modrinth"))
        self.provider_combo.setItemText(1, tr("mods.catalog.provider.curseforge"))
        self.loader_label.setText(tr("mods.catalog.loader.label"))
        self.loader_combo.setItemText(0, tr("modrinth.loader.fabric"))
        self.loader_combo.setItemText(1, tr("modrinth.loader.forge"))
        self.search_button.setText(tr("common.search"))
        self.clear_cache_button.setText(tr("curseforge.cache.clear"))
        self.previous_button.setText(tr("common.previous"))
        self.next_button.setText(tr("common.next"))
        self.install_button.setText(tr("mods.catalog.choose_instance"))
        self.include_beta_checkbox.setText(tr("modrinth.channel.beta"))
        self.include_alpha_checkbox.setText(tr("modrinth.channel.alpha"))
        self._update_provider_ui()
        if self._result is None:
            self._reset_catalog()
