from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QPushButton

from src.gui.config import NAVIGATION_ITEMS
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class LauncherSettingsPage(BasePage):
    save_requested = Signal(dict)
    reset_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Launcher Settings", "Preferences here belong to the GUI, not to an individual Minecraft instance.")
        self._build_ui()

    def _build_ui(self) -> None:
        behavior_card = CardWidget("Startup and behavior")
        self.start_page_combo = QComboBox()
        for page_id, label in NAVIGATION_ITEMS:
            self.start_page_combo.addItem(label, page_id)
        self.show_snapshots = QCheckBox("Show non-release versions by default")
        self.remember_window_size = QCheckBox("Remember window size and position")
        self.debug_mode = QCheckBox("Enable debug launch information")
        behavior_card.layout.addWidget(QLabel("Startup page"))
        behavior_card.layout.addWidget(self.start_page_combo)
        behavior_card.layout.addWidget(self.show_snapshots)
        behavior_card.layout.addWidget(self.remember_window_size)
        behavior_card.layout.addWidget(self.debug_mode)
        self.root_layout.addWidget(behavior_card)

        appearance_card = CardWidget("Appearance", "The current stylesheet is intentionally text-only so custom icons and pixel assets can be added later.")
        theme_value = QLabel("Theme: MCW Dark Block")
        theme_value.setObjectName("ValueLabel")
        appearance_card.layout.addWidget(theme_value)
        self.root_layout.addWidget(appearance_card)

        save_button = QPushButton("Save launcher settings")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(lambda: self.save_requested.emit(self.form_data()))
        reset_button = QPushButton("Reset to defaults")
        reset_button.clicked.connect(self.reset_requested.emit)
        self.root_layout.addWidget(save_button)
        self.root_layout.addWidget(reset_button)
        self.root_layout.addStretch()

    def set_settings(self, settings: dict) -> None:
        index = self.start_page_combo.findData(settings.get("start_page", "home"))
        self.start_page_combo.setCurrentIndex(max(0, index))
        self.show_snapshots.setChecked(bool(settings.get("show_snapshots", False)))
        self.debug_mode.setChecked(bool(settings.get("debug_mode", False)))
        self.remember_window_size.setChecked(bool(settings.get("remember_window_size", True)))

    def form_data(self) -> dict:
        return {
            "start_page": self.start_page_combo.currentData(),
            "show_snapshots": self.show_snapshots.isChecked(),
            "debug_mode": self.debug_mode.isChecked(),
            "remember_window_size": self.remember_window_size.isChecked(),
        }
