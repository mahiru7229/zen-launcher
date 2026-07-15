from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit

from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget
from src.gui.theme.runtime import set_theme_icon


class InstanceSettingsPage(BasePage):
    load_requested = Signal(str)
    save_requested = Signal(str, dict)

    def __init__(self) -> None:
        super().__init__("Instance Settings", "Settings are loaded and saved through the public SettingsManager API.", "instance_settings")
        self._build_ui()

    def _build_ui(self) -> None:
        selector_card = CardWidget("Target instance")
        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self.load_requested.emit)
        reload_button = set_theme_icon(QPushButton("Reload settings"), "icon.action.refresh")
        reload_button.clicked.connect(lambda: self.load_requested.emit(self.current_instance_name()))
        selector_card.layout.addWidget(self.instance_combo)
        selector_card.layout.addWidget(reload_button)
        self.root_layout.addWidget(selector_card)

        java_card = CardWidget("Java and memory")
        self.java_path_input = QLineEdit()
        self.java_path_input.setPlaceholderText("Leave empty for automatic Java selection")
        browse_button = set_theme_icon(QPushButton("Browse Java executable"), "icon.action.folder")
        browse_button.clicked.connect(self._browse_java)
        memory_grid = QGridLayout()
        self.min_memory = QSpinBox()
        self.max_memory = QSpinBox()
        for spin_box in (self.min_memory, self.max_memory):
            spin_box.setRange(256, 65536)
            spin_box.setSingleStep(256)
            spin_box.setSuffix(" MB")
        memory_grid.addWidget(QLabel("Minimum memory"), 0, 0)
        memory_grid.addWidget(self.min_memory, 1, 0)
        memory_grid.addWidget(QLabel("Maximum memory"), 0, 1)
        memory_grid.addWidget(self.max_memory, 1, 1)
        java_card.layout.addWidget(self.java_path_input)
        java_card.layout.addWidget(browse_button)
        java_card.layout.addLayout(memory_grid)
        self.root_layout.addWidget(java_card)

        window_card = CardWidget("Game window")
        window_grid = QGridLayout()
        self.window_width = QSpinBox()
        self.window_height = QSpinBox()
        for spin_box in (self.window_width, self.window_height):
            spin_box.setRange(320, 7680)
        self.fullscreen = QCheckBox("Launch in fullscreen")
        self.offline_multiplayer = QCheckBox("Enable offline multiplayer workaround")
        window_grid.addWidget(QLabel("Width"), 0, 0)
        window_grid.addWidget(self.window_width, 1, 0)
        window_grid.addWidget(QLabel("Height"), 0, 1)
        window_grid.addWidget(self.window_height, 1, 1)
        window_card.layout.addLayout(window_grid)
        window_card.layout.addWidget(self.fullscreen)
        window_card.layout.addWidget(self.offline_multiplayer)
        self.root_layout.addWidget(window_card)

        modrinth_card = CardWidget(
            "Modrinth downloads",
            "Recommended: keep this enabled. Turn it off only when you plan to download failed modpack files manually.",
        )
        self.block_modrinth_failure = QCheckBox("Stop launch when required Modrinth files are missing")
        self.block_modrinth_failure.setChecked(True)
        self.block_modrinth_failure.setToolTip(
            "This option belongs to the selected instance. Disable it to let Minecraft launch after three failed download rounds, then place the missing files manually in the paths shown by the launcher."
        )
        modrinth_card.layout.addWidget(self.block_modrinth_failure)
        self.root_layout.addWidget(modrinth_card)

        arguments_card = CardWidget("Custom arguments", "Enter one argument per line.")
        self.jvm_arguments = QTextEdit()
        self.jvm_arguments.setObjectName("ArgumentEditor")
        self.jvm_arguments.setPlaceholderText("JVM arguments")
        self.jvm_arguments.setFixedHeight(90)
        self.game_arguments = QTextEdit()
        self.game_arguments.setObjectName("ArgumentEditor")
        self.game_arguments.setPlaceholderText("Game arguments")
        self.game_arguments.setFixedHeight(90)
        arguments_card.layout.addWidget(QLabel("JVM arguments"))
        arguments_card.layout.addWidget(self.jvm_arguments)
        arguments_card.layout.addWidget(QLabel("Game arguments"))
        arguments_card.layout.addWidget(self.game_arguments)
        self.root_layout.addWidget(arguments_card)

        save_button = set_theme_icon(QPushButton("Save instance settings"), "icon.action.save")
        save_button.setObjectName("PrimaryButton")
        save_button.setMinimumHeight(48)
        save_button.clicked.connect(lambda: self.save_requested.emit(self.current_instance_name(), self.form_data()))
        self.root_layout.addWidget(save_button)
        self.root_layout.addStretch()

    def set_instances(self, instances: list, selected_name: str) -> None:
        self.instance_combo.blockSignals(True)
        self.instance_combo.clear()
        self.instance_combo.addItems([instance.name for instance in instances])
        if selected_name:
            self.instance_combo.setCurrentText(selected_name)
        self.instance_combo.blockSignals(False)

    def select_instance(self, name: str) -> None:
        self.instance_combo.blockSignals(True)
        self.instance_combo.setCurrentText(name)
        self.instance_combo.blockSignals(False)

    def current_instance_name(self) -> str:
        return self.instance_combo.currentText().strip()

    def set_settings(self, instance_name: str, settings: object | None) -> None:
        if settings is None:
            self._clear_form()
            return
        if instance_name and self.instance_combo.currentText() != instance_name:
            self.instance_combo.blockSignals(True)
            self.instance_combo.setCurrentText(instance_name)
            self.instance_combo.blockSignals(False)
        self.java_path_input.setText(str(getattr(settings, "java_path", "") or ""))
        self.min_memory.setValue(int(getattr(settings, "min_memory", 1024)))
        self.max_memory.setValue(int(getattr(settings, "max_memory", 2048)))
        self.window_width.setValue(int(getattr(settings, "width", 1280)))
        self.window_height.setValue(int(getattr(settings, "height", 720)))
        self.fullscreen.setChecked(bool(getattr(settings, "fullscreen", False)))
        self.offline_multiplayer.setChecked(bool(getattr(settings, "offline_multiplayer_enabled", False)))
        self.block_modrinth_failure.setChecked(bool(getattr(settings, "block_launch_on_modrinth_failure", True)))
        self.jvm_arguments.setPlainText("\n".join(getattr(settings, "jvm_arguments", [])))
        self.game_arguments.setPlainText("\n".join(getattr(settings, "game_arguments", [])))

    def form_data(self) -> dict:
        return {
            "java_path": self.java_path_input.text(),
            "min_memory": self.min_memory.value(),
            "max_memory": self.max_memory.value(),
            "width": self.window_width.value(),
            "height": self.window_height.value(),
            "fullscreen": self.fullscreen.isChecked(),
            "offline_multiplayer_enabled": self.offline_multiplayer.isChecked(),
            "block_launch_on_modrinth_failure": self.block_modrinth_failure.isChecked(),
            "jvm_arguments": self._lines(self.jvm_arguments.toPlainText()),
            "game_arguments": self._lines(self.game_arguments.toPlainText()),
        }

    def set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)

    def _browse_java(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose Java executable", "", "Java executable (java.exe javaw.exe);;All files (*)")
        if path:
            self.java_path_input.setText(path)

    def _clear_form(self) -> None:
        self.java_path_input.clear()
        self.min_memory.setValue(1024)
        self.max_memory.setValue(2048)
        self.window_width.setValue(1280)
        self.window_height.setValue(720)
        self.fullscreen.setChecked(False)
        self.offline_multiplayer.setChecked(False)
        self.block_modrinth_failure.setChecked(True)
        self.jvm_arguments.clear()
        self.game_arguments.clear()

    @staticmethod
    def _lines(text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]
