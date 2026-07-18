from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from src.core.curseforge.curseforge_registry import CurseForgeRegistry
from src.core.language.language_manager import tr
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.gui.theme.runtime import set_theme_icon
from src.models.instance.instance import Instance
from src.models.mod.mod_info import ModInfo
from src.models.mod.mod_issue import ModHealthReport, ModIssue
from src.models.modrinth.update import ModrinthModUpdateEntry, ModrinthModUpdateReport


class ModManagerDialog(QDialog):
    refresh_requested = Signal()
    add_requested = Signal(list, bool)
    remove_requested = Signal(list)
    enabled_requested = Signal(list, bool)
    modrinth_requested = Signal()
    curseforge_requested = Signal()
    check_updates_requested = Signal(object)
    update_projects_requested = Signal(list, object)
    update_all_requested = Signal(object)
    lock_requested = Signal(list, bool)
    analyze_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._instance: Instance | None = None
        self._mods: list[ModInfo] = []
        self._updates = ModrinthModUpdateReport(entries=())
        self._health = ModHealthReport(issues=(), enabled_mods=0, disabled_mods=0)
        self._include_beta = False
        self._include_alpha = False
        self._busy = False
        self._updates_checked = False
        self._update_checking = False
        self._update_error = ""
        self.setWindowTitle("Mod Manager")
        self.setObjectName("ModManagerDialog")
        self.resize(1260, 760)
        self.setAcceptDrops(True)
        self._build_ui()

    @property
    def allowed_version_types(self) -> tuple[str, ...]:
        values = ["release"]
        if self._include_beta:
            values.append("beta")
        if self._include_alpha:
            values.append("alpha")
        return tuple(values)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.title_label = QLabel("No instance selected")
        self.title_label.setObjectName("PageTitle")
        self.summary_label = QLabel("Choose a Fabric or Forge instance to manage its mods.")
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        self.health_label = QLabel("")
        self.health_label.setObjectName("MutedLabel")
        self.health_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.summary_label)
        root.addWidget(self.health_label)

        self.update_notice_label = QLabel("")
        self.update_notice_label.setObjectName("StatusBadge")
        self.update_notice_label.setWordWrap(True)
        self.update_notice_label.hide()
        root.addWidget(self.update_notice_label)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name, mod id, version, source, update, or file...")
        self.search_input.textChanged.connect(self._apply_filter)
        self.refresh_button = set_theme_icon(QPushButton("Refresh"), "icon.action.refresh")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.open_folder_button = set_theme_icon(QPushButton("Open mod folder"), "icon.action.folder")
        self.open_folder_button.clicked.connect(self._open_folder)
        self.analyze_button = set_theme_icon(QPushButton("Analyze dependencies"), "icon.action.repair")
        self.analyze_button.clicked.connect(self.analyze_requested.emit)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.refresh_button)
        search_row.addWidget(self.analyze_button)
        search_row.addWidget(self.open_folder_button)
        root.addLayout(search_row)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["State", "Name", "Version", "Source", "Update", "Lock", "Mod ID", "Environment", "Status", "File"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        root.addWidget(self.table, 1)

        update_row = QHBoxLayout()
        self.check_updates_button = set_theme_icon(QPushButton("Check updates"), "icon.action.refresh")
        self.update_selected_button = set_theme_icon(QPushButton("Update selected"), "icon.action.download")
        self.update_all_button = set_theme_icon(QPushButton("Update all"), "icon.action.download")
        self.lock_button = QPushButton("Lock version")
        self.unlock_button = QPushButton("Unlock version")
        self.check_updates_button.clicked.connect(lambda: self.check_updates_requested.emit(self.allowed_version_types))
        self.update_selected_button.clicked.connect(self._request_update_selected)
        self.update_all_button.clicked.connect(self._request_update_all)
        self.lock_button.clicked.connect(lambda: self._request_lock(True))
        self.unlock_button.clicked.connect(lambda: self._request_lock(False))
        update_row.addWidget(self.check_updates_button)
        update_row.addWidget(self.update_selected_button)
        update_row.addWidget(self.update_all_button)
        update_row.addWidget(self.lock_button)
        update_row.addWidget(self.unlock_button)
        update_row.addStretch()
        root.addLayout(update_row)

        action_row = QHBoxLayout()
        self.add_button = set_theme_icon(QPushButton("Add mod files"), "icon.action.add")
        self.add_button.setObjectName("PrimaryButton")
        self.modrinth_button = set_theme_icon(QPushButton("Browse Modrinth"), "icon.action.modrinth")
        self.curseforge_button = set_theme_icon(QPushButton("Browse CurseForge"), "icon.action.download")
        self.enable_button = set_theme_icon(QPushButton("Enable"), "icon.action.enable")
        self.disable_button = set_theme_icon(QPushButton("Disable"), "icon.action.disable")
        self.remove_button = set_theme_icon(QPushButton("Remove"), "icon.action.remove")
        self.remove_button.setObjectName("DangerButton")
        self.add_button.clicked.connect(self._choose_add)
        self.modrinth_button.clicked.connect(self.modrinth_requested.emit)
        self.curseforge_button.clicked.connect(self.curseforge_requested.emit)
        self.enable_button.clicked.connect(lambda: self._request_enabled(True))
        self.disable_button.clicked.connect(lambda: self._request_enabled(False))
        self.remove_button.clicked.connect(self._request_remove)
        action_row.addWidget(self.add_button)
        action_row.addWidget(self.modrinth_button)
        action_row.addWidget(self.curseforge_button)
        action_row.addWidget(self.enable_button)
        action_row.addWidget(self.disable_button)
        action_row.addWidget(self.remove_button)
        action_row.addStretch()
        root.addLayout(action_row)

        self.details = QPlainTextEdit()
        self.details.setObjectName("DetailsOutput")
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a mod to view metadata, dependencies, update state, and compatibility issues.")
        self.details.setMaximumHeight(210)
        root.addWidget(self.details)

    def set_instance(self, instance: Instance | None) -> None:
        self._instance = instance
        self._mods = []
        self._updates = ModrinthModUpdateReport(entries=())
        self._health = ModHealthReport(issues=(), enabled_mods=0, disabled_mods=0)
        self._updates_checked = False
        self._update_checking = False
        self._update_error = ""
        self.table.setRowCount(0)
        self.details.clear()
        self.health_label.clear()
        self._render_update_notice()

        if instance is None:
            self.title_label.setText(tr("No instance selected"))
            self.summary_label.setText(tr("Choose a Fabric or Forge instance to manage its mods."))
            self._set_actions_enabled(False)
            return

        loader_name, loader_version = ModLoaderManager.normalize(instance.mod_loader)
        self.title_label.setText(tr("Mods — {name}", name=instance.name))
        if loader_name in {ModLoaderManager.FABRIC, ModLoaderManager.FORGE}:
            loader_title = "Fabric Loader" if loader_name == ModLoaderManager.FABRIC else "Minecraft Forge"
            self.summary_label.setText(tr("Minecraft {version} • {loader} {loader_version} • Drop .jar files into this window to add them.", version=instance.version_id, loader=loader_title, loader_version=loader_version))
            self._set_actions_enabled(not self._busy)
        else:
            self.summary_label.setText(tr("This instance is Vanilla. Apply Fabric or Forge from the Instances page before adding mods."))
            self._set_actions_enabled(False)

    def set_mods(self, mods: list[ModInfo]) -> None:
        self._mods = list(mods)
        self._render_table()
        self._render_summary()

    def set_update_report(self, report: ModrinthModUpdateReport) -> None:
        self._updates = report if isinstance(report, ModrinthModUpdateReport) else ModrinthModUpdateReport(entries=())
        self._updates_checked = True
        self._update_checking = False
        self._update_error = ""
        self._render_table()
        self._render_summary()
        self._render_update_notice()

    def set_update_checking(self, checking: bool) -> None:
        self._update_checking = bool(checking)
        if checking:
            self._update_error = ""
        self._set_actions_enabled(not self._busy and self._is_modded_instance())
        self._render_update_notice()

    def set_update_error(self, message: str) -> None:
        self._update_checking = False
        self._updates_checked = True
        self._update_error = str(message).strip()
        self._render_update_notice()

    def set_health_report(self, report: ModHealthReport) -> None:
        self._health = report if isinstance(report, ModHealthReport) else ModHealthReport(issues=(), enabled_mods=0, disabled_mods=0)
        self._render_table()
        self._render_summary()

    def set_channel_preferences(self, include_beta: bool, include_alpha: bool) -> None:
        self._include_beta = bool(include_beta)
        self._include_alpha = bool(include_alpha)

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self._set_actions_enabled(not self._busy and self._is_modded_instance())

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        paths = self._jar_paths_from_urls(event.mimeData().urls())
        if paths and self._is_modded_instance() and not self._busy:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._jar_paths_from_urls(event.mimeData().urls())
        if paths and self._is_modded_instance() and not self._busy:
            self._request_add(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _render_table(self) -> None:
        selected_files = {mod.file_name.casefold() for mod in self._selected_mods()}
        updates = self._updates_by_file()
        issues = self._issues_by_mod_id()
        curseforge_files = self._curseforge_files()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._mods))

        for row, mod in enumerate(self._mods):
            update = updates.get(mod.file_name.casefold())
            mod_issues = issues.get(mod.mod_id.casefold(), ())
            if update is not None:
                source = tr("mod_manager.source.modrinth")
            elif mod.file_name.casefold() in curseforge_files:
                source = tr("mod_manager.source.curseforge")
            else:
                source = tr("mod_manager.source.local")
            update_text = "—"
            lock_text = "—"
            if update is not None:
                update_text = tr(f"mod_manager.update.status.{update.status.casefold().replace(' ', '_')}", default=update.status)
                if update.update_available and not update.warning:
                    update_text = f"{update.current_version_number} → {update.latest_version_number}"
                lock_text = tr("mod_manager.lock.locked") if update.locked else tr("mod_manager.lock.unlocked")
            status = tr(mod.status)
            if mod_issues:
                errors = sum(1 for issue in mod_issues if issue.severity == "error")
                warnings = sum(1 for issue in mod_issues if issue.severity == "warning")
                status = f"{status} • {errors}E/{warnings}W"
            values = [tr("Enabled" if mod.enabled else "Disabled"), mod.name, mod.version, source, update_text, lock_text, mod.mod_id, mod.environment, status, mod.file_name]
            tooltip = "\n".join(issue.message for issue in mod_issues)
            if mod.error:
                tooltip = "\n".join(item for item in (mod.error, tooltip) if item)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, mod)
                if tooltip:
                    item.setToolTip(tooltip)
                self.table.setItem(row, column, item)

        self.table.setSortingEnabled(True)
        self._apply_filter()
        if selected_files:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                mod = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
                if isinstance(mod, ModInfo) and mod.file_name.casefold() in selected_files:
                    self.table.selectRow(row)
        self._update_action_state()
        self._render_details()

    def _render_summary(self) -> None:
        if self._instance is None or not self._is_modded_instance():
            return
        enabled_count = sum(1 for mod in self._mods if mod.enabled)
        self.summary_label.setText(tr("{count} mod(s) found • {enabled_count} enabled • {path}", count=len(self._mods), enabled_count=enabled_count, path=self._instance.instance_dir / "mods"))
        tracked = len(self._updates.entries)
        channels = "/".join(item.title() for item in self.allowed_version_types)
        self.health_label.setText(tr("mod_manager.health_summary", errors=self._health.error_count, warnings=self._health.warning_count, tracked=tracked, updates=self._updates.update_count, channels=channels))

    def _render_update_notice(self) -> None:
        if self._instance is None or not self._is_fabric_instance():
            self.update_notice_label.clear()
            self.update_notice_label.hide()
            return

        if self._update_checking:
            self._set_update_notice(tr("mod_manager.update_notice.checking"), warning=True)
            return

        if self._update_error:
            self._set_update_notice(tr("mod_manager.update_notice.failed", error=self._update_error), warning=True)
            return

        if not self._updates_checked:
            self.update_notice_label.clear()
            self.update_notice_label.hide()
            return

        available = [entry for entry in self._updates.entries if entry.update_available and not entry.file_missing and not entry.warning]
        if available:
            shown = available[:3]
            descriptions: list[str] = []
            for entry in shown:
                detail = f"{entry.title}: {entry.current_version_number} → {entry.latest_version_number}"
                descriptions.append(tr("mod_manager.update_notice.locked_detail", detail=detail) if entry.locked else detail)
            details = ", ".join(descriptions)
            remaining = len(available) - len(shown)
            if remaining > 0:
                details = tr("mod_manager.update_notice.available_more", details=details, remaining=remaining)
            self._set_update_notice(tr("mod_manager.update_notice.available", count=len(available), details=details), warning=True)
            return

        failed = [entry for entry in self._updates.entries if entry.file_missing or entry.warning]
        if failed:
            self._set_update_notice(tr("mod_manager.update_notice.partial_failed", count=len(failed)), warning=True)
            return

        if not self._updates.entries:
            self._set_update_notice(tr("mod_manager.update_notice.not_tracked"), warning=False)
            return

        self._set_update_notice(tr("mod_manager.update_notice.up_to_date"), warning=False)

    def _set_update_notice(self, text: str, warning: bool) -> None:
        object_name = "WarningBadge" if warning else "StatusBadge"
        if self.update_notice_label.objectName() != object_name:
            self.update_notice_label.setObjectName(object_name)
            self.update_notice_label.style().unpolish(self.update_notice_label)
            self.update_notice_label.style().polish(self.update_notice_label)
        self.update_notice_label.setText(text)
        self.update_notice_label.show()

    def _selection_changed(self) -> None:
        self._render_details()
        self._update_action_state()

    def _choose_add(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, tr("Add Fabric mods"), "", tr("Fabric mods (*.jar)"))
        if files:
            self._request_add([Path(file) for file in files])

    def _request_add(self, paths: list[Path]) -> None:
        existing_names = {mod.file_name.casefold() for mod in self._mods}
        conflicts = [path.name for path in paths if path.name.casefold() in existing_names]
        replace = False
        if conflicts:
            answer = QMessageBox.question(self, tr("Replace mods"), tr("The following files already exist:\n\n{files}\n\nReplace them?", files="\n".join(conflicts)), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            replace = True
        self.add_requested.emit(paths, replace)

    def _request_remove(self) -> None:
        paths = self._selected_paths()
        if not paths:
            return
        answer = QMessageBox.question(self, tr("Remove mods"), tr("Remove {count} selected mod file(s)?", count=len(paths)), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(paths)

    def _request_enabled(self, enabled: bool) -> None:
        paths = self._selected_paths()
        if paths:
            self.enabled_requested.emit(paths, enabled)

    def _request_update_selected(self) -> None:
        project_ids = [entry.project_id for entry in self._selected_update_entries() if entry.update_available and not entry.locked and not entry.warning and not entry.file_missing]
        if not project_ids:
            return
        answer = QMessageBox.question(self, tr("Update mods"), tr("Update {count} selected Modrinth mod(s)?", count=len(project_ids)), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.update_projects_requested.emit(project_ids, self.allowed_version_types)

    def _request_update_all(self) -> None:
        count = self._updates.update_count
        if count < 1:
            QMessageBox.information(self, tr("Update mods"), tr("All unlocked Modrinth mods are up to date."))
            return
        answer = QMessageBox.question(self, tr("Update mods"), tr("Update all {count} unlocked Modrinth mod(s)?", count=count), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.update_all_requested.emit(self.allowed_version_types)

    def _request_lock(self, locked: bool) -> None:
        project_ids = [entry.project_id for entry in self._selected_update_entries()]
        if project_ids:
            self.lock_requested.emit(project_ids, locked)

    def _selected_paths(self) -> list[Path]:
        return [mod.path for mod in self._selected_mods()]

    def _selected_mods(self) -> list[ModInfo]:
        mods: list[ModInfo] = []
        selection = self.table.selectionModel()
        if selection is None:
            return mods
        for index in selection.selectedRows():
            item = self.table.item(index.row(), 0)
            mod = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
            if isinstance(mod, ModInfo):
                mods.append(mod)
        return mods

    def _selected_update_entries(self) -> list[ModrinthModUpdateEntry]:
        updates = self._updates_by_file()
        return [updates[mod.file_name.casefold()] for mod in self._selected_mods() if mod.file_name.casefold() in updates]

    def _render_details(self) -> None:
        selected_mods = self._selected_mods()
        if not selected_mods:
            self.details.clear()
            return
        mod = selected_mods[0]
        update = self._updates_by_file().get(mod.file_name.casefold())
        mod_issues = self._issues_by_mod_id().get(mod.mod_id.casefold(), ())
        dependencies = "\n".join(f"  {name}: {requirement}" for name, requirement in mod.dependencies.items()) or tr("  None declared")
        authors = ", ".join(mod.authors) or tr("Unknown")
        licenses = ", ".join(mod.licenses) or tr("Unknown")
        text = [f"{mod.name} ({mod.mod_id})", tr("Version: {version}", version=mod.version), tr("State: {state}", state=tr("Enabled" if mod.enabled else "Disabled")), tr("Environment: {environment}", environment=mod.environment), tr("Authors: {authors}", authors=authors), tr("License: {licenses}", licenses=licenses), tr("Status: {status}", status=tr(mod.status)), "", mod.description or tr("No description."), "", tr("Dependencies:"), dependencies]
        if update is not None:
            text.extend(["", "Modrinth:", f"  Project: {update.title} ({update.project_id})", f"  Installed: {update.current_version_number}", f"  Latest allowed: {update.latest_version_number} ({update.latest_version_type})", f"  Version lock: {'On' if update.locked else 'Off'}", f"  Update state: {update.status}"])
            if update.warning:
                text.append(f"  Warning: {update.warning}")
        if mod_issues:
            text.extend(["", "Compatibility issues:"])
            text.extend(f"  [{issue.severity.upper()}] {issue.message}" for issue in mod_issues)
        if mod.error:
            text.extend(["", tr("Warning:"), mod.error])
        self.details.setPlainText("\n".join(text))

    def _apply_filter(self) -> None:
        query = self.search_input.text().strip().casefold()
        for row in range(self.table.rowCount()):
            values = [self.table.item(row, column).text() for column in range(self.table.columnCount()) if self.table.item(row, column) is not None]
            self.table.setRowHidden(row, bool(query and query not in " ".join(values).casefold()))

    def _open_folder(self) -> None:
        if self._instance is not None:
            folder = self._instance.instance_dir / "mods"
            folder.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def _set_actions_enabled(self, enabled: bool) -> None:
        for button in (self.refresh_button, self.analyze_button, self.open_folder_button, self.add_button, self.enable_button, self.disable_button, self.remove_button):
            button.setEnabled(enabled)
        self.modrinth_button.setEnabled(enabled and self._is_fabric_instance())
        self.curseforge_button.setEnabled(enabled and self._is_forge_instance())
        self.check_updates_button.setEnabled(enabled and not self._update_checking)
        self._update_action_state()

    def _update_action_state(self) -> None:
        enabled = not self._busy and self._is_fabric_instance()
        selected = self._selected_update_entries()
        self.update_selected_button.setEnabled(enabled and any(entry.update_available and not entry.locked and not entry.warning and not entry.file_missing for entry in selected))
        self.update_all_button.setEnabled(enabled and self._updates.update_count > 0)
        self.lock_button.setEnabled(enabled and any(not entry.locked for entry in selected))
        self.unlock_button.setEnabled(enabled and any(entry.locked for entry in selected))

    def _updates_by_file(self) -> dict[str, ModrinthModUpdateEntry]:
        return {entry.file_name.casefold(): entry for entry in self._updates.entries if entry.file_name}

    def _issues_by_mod_id(self) -> dict[str, tuple[ModIssue, ...]]:
        result: dict[str, list[ModIssue]] = {}
        for issue in self._health.issues:
            for mod_id in issue.mod_ids:
                result.setdefault(mod_id.casefold(), []).append(issue)
        return {key: tuple(value) for key, value in result.items()}

    def _is_fabric_instance(self) -> bool:
        if self._instance is None:
            return False
        loader_name, _ = ModLoaderManager.normalize(self._instance.mod_loader)
        return loader_name == ModLoaderManager.FABRIC

    def _is_forge_instance(self) -> bool:
        if self._instance is None:
            return False
        loader_name, _ = ModLoaderManager.normalize(self._instance.mod_loader)
        return loader_name == ModLoaderManager.FORGE

    def _is_modded_instance(self) -> bool:
        return self._is_fabric_instance() or self._is_forge_instance()

    def _curseforge_files(self) -> set[str]:
        if self._instance is None:
            return set()
        registry = CurseForgeRegistry.load(self._instance)
        mods = registry.get("mods", {}) if isinstance(registry, dict) else {}
        return {str(entry.get("fileName") or "").casefold() for entry in mods.values() if isinstance(entry, dict) and str(entry.get("fileName") or "").strip()}

    def retranslate_dynamic(self) -> None:
        instance = self._instance
        mods = list(self._mods)
        updates = self._updates
        health = self._health
        self.set_instance(instance)
        if instance is not None:
            self._mods = mods
            self._updates = updates
            self._health = health
            self._render_table()
            self._render_summary()
            self._render_update_notice()
        self.refresh_button.setText(tr("mod_manager.refresh"))
        self.open_folder_button.setText(tr("mod_manager.open_folder"))
        self.analyze_button.setText(tr("mod_manager.analyze"))
        self.check_updates_button.setText(tr("mod_manager.check_updates"))
        self.update_selected_button.setText(tr("mod_manager.update_selected"))
        self.update_all_button.setText(tr("mod_manager.update_all"))
        self.lock_button.setText(tr("mod_manager.lock_version"))
        self.unlock_button.setText(tr("mod_manager.unlock_version"))
        self.add_button.setText(tr("mod_manager.add_files"))
        self.enable_button.setText(tr("mod_manager.enable"))
        self.disable_button.setText(tr("mod_manager.disable"))
        self.remove_button.setText(tr("mod_manager.remove"))
        self.modrinth_button.setText(tr("modrinth.browse"))
        self.curseforge_button.setText(tr("curseforge.browse"))

    @staticmethod
    def _jar_paths_from_urls(urls: list[QUrl]) -> list[Path]:
        paths = [Path(url.toLocalFile()) for url in urls if url.isLocalFile()]
        return [path for path in paths if path.is_file() and path.suffix.lower() == ".jar"]
