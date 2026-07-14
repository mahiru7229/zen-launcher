from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit, QMessageBox, QPushButton

from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class InstancesPage(BasePage):
    refresh_requested = Signal()
    selected_instance_changed = Signal(str)
    create_requested = Signal(str, str)
    rename_requested = Signal(str, str)
    clone_requested = Signal(str, str, bool)
    delete_requested = Signal(str)
    import_requested = Signal(object)
    export_requested = Signal(str, object, bool)

    def __init__(self) -> None:
        super().__init__("Instances", "Create, clone, rename, import, export, and choose the instance used by the launch bar.")
        self._instances: dict[str, object] = {}
        self._versions: list[object] = []
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

        create_card = CardWidget("Create instance", "Version metadata is loaded through VersionManager on a worker thread.")
        self.create_name_input = QLineEdit()
        self.create_name_input.setPlaceholderText("New instance name")
        self.version_combo = QComboBox()
        self.snapshot_checkbox = QCheckBox("Show snapshots, old alpha, and old beta")
        self.snapshot_checkbox.toggled.connect(self._apply_version_filter)
        create_button = QPushButton("Create instance")
        create_button.setObjectName("PrimaryButton")
        create_button.clicked.connect(lambda: self.create_requested.emit(self.create_name_input.text(), self.version_combo.currentText()))
        create_card.layout.addWidget(QLabel("Name"))
        create_card.layout.addWidget(self.create_name_input)
        create_card.layout.addWidget(QLabel("Minecraft version"))
        create_card.layout.addWidget(self.version_combo)
        create_card.layout.addWidget(self.snapshot_checkbox)
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
        rename_button.clicked.connect(lambda: self.rename_requested.emit(self.current_instance_name(), self.target_name_input.text()))
        clone_button.clicked.connect(lambda: self.clone_requested.emit(self.current_instance_name(), self.target_name_input.text(), self.include_saves_checkbox.isChecked()))
        delete_button.clicked.connect(self._confirm_delete)
        import_button.clicked.connect(self._choose_import)
        export_button.clicked.connect(self._choose_export)
        action_grid.addWidget(rename_button, 0, 0)
        action_grid.addWidget(clone_button, 0, 1)
        action_grid.addWidget(delete_button, 0, 2)
        action_grid.addWidget(import_button, 1, 0, 1, 2)
        action_grid.addWidget(export_button, 1, 2)
        manage_card.layout.addWidget(QLabel("Target name"))
        manage_card.layout.addWidget(self.target_name_input)
        manage_card.layout.addWidget(self.include_saves_checkbox)
        manage_card.layout.addLayout(action_grid)
        self.root_layout.addWidget(manage_card)
        self.root_layout.addStretch()

    def set_versions(self, versions: list) -> None:
        self._versions = list(versions)
        self._apply_version_filter()

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
        loader = getattr(instance, "mod_loader", ("vanilla", "-1"))
        self.instance_info.setText(f"Minecraft {instance.version_id} • {loader[0]} • {instance.instance_dir}")
        self.target_name_input.setText(instance.name)
        self.version_combo.setCurrentText(instance.version_id)

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
