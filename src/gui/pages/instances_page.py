from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class InstancesPage(BasePage):
    refresh_requested = Signal()
    selected_instance_changed = Signal(str)
    create_requested = Signal(str, str, str, str)
    rename_requested = Signal(str, str)
    clone_requested = Signal(str, str, bool)
    delete_requested = Signal(str)
    import_requested = Signal(object)
    export_requested = Signal(str, object, bool)
    fabric_versions_requested = Signal(str)
    loader_change_requested = Signal(str, str, str)
    manage_mods_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("Instances", "Create and manage isolated Minecraft instances, including Fabric Loader and per-instance mods.")
        self._instances: dict[str, object] = {}
        self._versions: list[object] = []
        self._fabric_versions: dict[str, list[object]] = {}
        self._pending_loader_version = ""
        self._synchronizing = False
        self._build_ui()

    def _build_ui(self) -> None:
        selected_card = CardWidget("Active instance")
        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self._instance_selected)
        self.instance_info = QLabel("No instance selected")
        self.instance_info.setObjectName("MutedLabel")
        refresh_button = QPushButton("Refresh instances")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        selected_card.layout.addWidget(self.instance_combo)
        selected_card.layout.addWidget(self.instance_info)
        selected_card.layout.addWidget(refresh_button)
        self.root_layout.addWidget(selected_card)

        create_card = CardWidget("Create instance", "Choose Vanilla or Fabric. Fabric metadata is installed and cached before the instance is created.")
        self.create_name_input = QLineEdit()
        self.create_name_input.setPlaceholderText("New instance name")
        self.version_combo = QComboBox()
        self.version_combo.currentTextChanged.connect(self._version_selected)
        self.snapshot_checkbox = QCheckBox("Show snapshots, old alpha, and old beta")
        self.snapshot_checkbox.toggled.connect(self._apply_version_filter)
        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["Vanilla", "Fabric"])
        self.loader_combo.currentTextChanged.connect(self._loader_selected)
        self.loader_version_combo = QComboBox()
        self.loader_version_combo.setEnabled(False)
        self.loader_status = QLabel("Vanilla does not require a loader version.")
        self.loader_status.setObjectName("MutedLabel")
        self.loader_status.setWordWrap(True)
        create_button = QPushButton("Create instance")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(self._request_create)
        create_card.layout.addWidget(QLabel("Name"))
        create_card.layout.addWidget(self.create_name_input)
        create_card.layout.addWidget(QLabel("Minecraft version"))
        create_card.layout.addWidget(self.version_combo)
        create_card.layout.addWidget(self.snapshot_checkbox)
        create_card.layout.addWidget(QLabel("Mod loader"))
        create_card.layout.addWidget(self.loader_combo)
        create_card.layout.addWidget(QLabel("Loader version"))
        create_card.layout.addWidget(self.loader_version_combo)
        create_card.layout.addWidget(self.loader_status)
        create_card.layout.addWidget(create_button)
        self.root_layout.addWidget(create_card)

        manage_card = CardWidget("Manage selected instance")
        self.target_name_input = QLineEdit()
        self.target_name_input.setPlaceholderText("New name or clone name")
        self.include_saves_checkbox = QCheckBox("Include saves when cloning or exporting")
        action_grid = QGridLayout()
        rename_button = QPushButton("Rename")
        clone_button = QPushButton("Clone")
        delete_button = QPushButton("Delete")
        delete_button.setObjectName("DangerButton")
        import_button = QPushButton("Import .mcwpack")
        export_button = QPushButton("Export .mcwpack")
        apply_loader_button = QPushButton("Apply selected loader")
        manage_mods_button = QPushButton("Manage mods")
        manage_mods_button.setObjectName("PrimaryButton")
        rename_button.clicked.connect(lambda: self.rename_requested.emit(self.current_instance_name(), self.target_name_input.text()))
        clone_button.clicked.connect(lambda: self.clone_requested.emit(self.current_instance_name(), self.target_name_input.text(), self.include_saves_checkbox.isChecked()))
        delete_button.clicked.connect(self._confirm_delete)
        import_button.clicked.connect(self._choose_import)
        export_button.clicked.connect(self._choose_export)
        apply_loader_button.clicked.connect(self._request_loader_change)
        manage_mods_button.clicked.connect(lambda: self.manage_mods_requested.emit(self.current_instance_name()))
        action_grid.addWidget(rename_button, 0, 0)
        action_grid.addWidget(clone_button, 0, 1)
        action_grid.addWidget(delete_button, 0, 2)
        action_grid.addWidget(import_button, 1, 0)
        action_grid.addWidget(export_button, 1, 1)
        action_grid.addWidget(apply_loader_button, 2, 0, 1, 2)
        action_grid.addWidget(manage_mods_button, 2, 2)
        manage_card.layout.addWidget(QLabel("Target name"))
        manage_card.layout.addWidget(self.target_name_input)
        manage_card.layout.addWidget(self.include_saves_checkbox)
        manage_card.layout.addLayout(action_grid)
        self.root_layout.addWidget(manage_card)
        self.root_layout.addStretch()

    def set_versions(self, versions: list) -> None:
        self._versions = list(versions)
        self._apply_version_filter()

    def set_fabric_versions(self, game_version: str, versions: list) -> None:
        self._fabric_versions[game_version] = list(versions)
        if self.version_combo.currentText() != game_version or self.loader_combo.currentText().casefold() != "fabric":
            return

        self.loader_version_combo.blockSignals(True)
        self.loader_version_combo.clear()
        for version in versions:
            label = version.version + (" (stable)" if getattr(version, "stable", False) else "")
            self.loader_version_combo.addItem(label, version.version)
        self.loader_version_combo.blockSignals(False)

        preferred = self._pending_loader_version
        self._pending_loader_version = ""
        if preferred:
            index = self.loader_version_combo.findData(preferred)
            if index >= 0:
                self.loader_version_combo.setCurrentIndex(index)
        elif versions:
            stable_index = next((index for index, version in enumerate(versions) if getattr(version, "stable", False)), 0)
            self.loader_version_combo.setCurrentIndex(stable_index)

        if versions:
            self.loader_status.setText(f"{len(versions)} compatible Fabric Loader version(s) found.")
        else:
            self.loader_status.setText("Fabric Loader is not available for this Minecraft version, or Fabric Meta could not be reached.")

    def set_instances(self, instances: list, selected_name: str) -> None:
        self._instances = {instance.name: instance for instance in instances}
        self._synchronizing = True
        self.instance_combo.blockSignals(True)
        self.instance_combo.clear()
        self.instance_combo.addItems([instance.name for instance in instances])
        if selected_name:
            self.instance_combo.setCurrentText(selected_name)
        self.instance_combo.blockSignals(False)
        self._synchronizing = False
        self._render_instance(self.instance_combo.currentText())

    def set_show_snapshots(self, enabled: bool) -> None:
        self.snapshot_checkbox.setChecked(enabled)

    def current_instance_name(self) -> str:
        return self.instance_combo.currentText().strip()

    def selected_loader(self) -> tuple[str, str]:
        loader_name = self.loader_combo.currentText().strip().lower()
        loader_version = str(self.loader_version_combo.currentData() or "").strip() if loader_name == "fabric" else "-1"
        return loader_name, loader_version

    def set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)

    def _apply_version_filter(self) -> None:
        selected = self.version_combo.currentText()
        include_all = self.snapshot_checkbox.isChecked()
        version_ids = [version.id for version in self._versions if include_all or getattr(version, "type", "") == "release"]
        self.version_combo.clear()
        self.version_combo.addItems(version_ids)
        if selected in version_ids:
            self.version_combo.setCurrentText(selected)

    def _version_selected(self, game_version: str) -> None:
        if self.loader_combo.currentText().casefold() == "fabric" and game_version:
            cached = self._fabric_versions.get(game_version)
            if cached is None:
                self.loader_status.setText("Loading Fabric Loader versions...")
                self.fabric_versions_requested.emit(game_version)
            else:
                self.set_fabric_versions(game_version, cached)

    def _loader_selected(self, loader_name: str) -> None:
        is_fabric = loader_name.casefold() == "fabric"
        self.loader_version_combo.setEnabled(is_fabric)
        if not is_fabric:
            self.loader_version_combo.clear()
            self.loader_status.setText("Vanilla does not require a loader version.")
            return
        self._version_selected(self.version_combo.currentText())

    def _instance_selected(self, name: str) -> None:
        self._render_instance(name)
        if not self._synchronizing:
            self.selected_instance_changed.emit(name if name in self._instances else "")

    def _render_instance(self, name: str) -> None:
        instance = self._instances.get(name)
        if instance is None:
            self.instance_info.setText("No instance selected")
            self.target_name_input.clear()
            return

        loader = tuple(getattr(instance, "mod_loader", ("vanilla", "-1")))
        loader_name = str(loader[0] if loader else "vanilla").lower()
        loader_version = str(loader[1] if len(loader) > 1 else "-1")
        loader_text = loader_name if loader_name == "vanilla" else f"{loader_name} {loader_version}"
        self.instance_info.setText(f"Minecraft {instance.version_id} • {loader_text} • {instance.instance_dir}")
        self.target_name_input.setText(instance.name)
        self.version_combo.setCurrentText(instance.version_id)
        self._pending_loader_version = loader_version
        self.loader_combo.setCurrentText("Fabric" if loader_name == "fabric" else "Vanilla")
        if loader_name == "fabric":
            self._version_selected(instance.version_id)

    def _request_create(self) -> None:
        loader_name, loader_version = self.selected_loader()
        self.create_requested.emit(self.create_name_input.text(), self.version_combo.currentText(), loader_name, loader_version)

    def _request_loader_change(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        loader_name, loader_version = self.selected_loader()
        self.loader_change_requested.emit(name, loader_name, loader_version)

    def _confirm_delete(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        answer = QMessageBox.question(self, "Delete instance", f"Delete '{name}' and its entire folder?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(name)

    def _choose_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import MCW instance", "", "MCW Package (*.mcwpack *.zip)")
        if path:
            self.import_requested.emit(Path(path))

    def _choose_export(self) -> None:
        name = self.current_instance_name()
        if not name:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export MCW instance", f"{name}.mcwpack", "MCW Package (*.mcwpack)")
        if path:
            output_path = Path(path)
            if output_path.suffix.lower() != ".mcwpack":
                output_path = output_path.with_suffix(".mcwpack")
            self.export_requested.emit(name, output_path, self.include_saves_checkbox.isChecked())
