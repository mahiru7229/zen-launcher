from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QPushButton

from src.core.language.language_manager import language_manager
from src.gui.config import NAVIGATION_ITEMS, VERSION
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class LauncherSettingsPage(BasePage):
    save_requested = Signal(dict)
    reset_requested = Signal()
    language_changed = Signal(str)
    check_updates_requested = Signal()

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

        language_card = CardWidget("Language", "Add another language by placing a compatible JSON file in the lang folder.")
        self.language_combo = QComboBox()
        self.reload_languages()
        self.language_combo.currentIndexChanged.connect(self._emit_language_changed)
        reload_languages_button = QPushButton("Reload language packs")
        reload_languages_button.clicked.connect(self.reload_languages)
        language_card.layout.addWidget(QLabel("Launcher language"))
        language_card.layout.addWidget(self.language_combo)
        language_card.layout.addWidget(reload_languages_button)
        self.root_layout.addWidget(language_card)

        update_card = CardWidget("Launcher updates", "MCW Launcher can check GitHub Releases and install ZIP updates after asking for confirmation.")
        current_version_label = QLabel(f"Current version: {VERSION}")
        current_version_label.setObjectName("ValueLabel")
        self.auto_check_updates = QCheckBox("Automatically check for updates when the launcher starts")
        self.update_channel_combo = QComboBox()
        self.update_channel_combo.addItem("Beta", "beta")
        self.update_channel_combo.addItem("Stable", "stable")
        self.update_status_label = QLabel("Update status: Not checked")
        self.update_status_label.setObjectName("ValueLabel")
        self.update_status_label.setWordWrap(True)
        self.check_updates_button = QPushButton("Check for updates")
        self.check_updates_button.clicked.connect(self.check_updates_requested.emit)
        update_card.layout.addWidget(current_version_label)
        update_card.layout.addWidget(self.auto_check_updates)
        update_card.layout.addWidget(QLabel("Update channel"))
        update_card.layout.addWidget(self.update_channel_combo)
        update_card.layout.addWidget(self.update_status_label)
        update_card.layout.addWidget(self.check_updates_button)
        self.root_layout.addWidget(update_card)

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

    def reload_languages(self) -> None:
        current_locale = self.language_combo.currentData() if hasattr(self, "language_combo") else None
        language_manager.reload()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for language in language_manager.available_languages():
            self.language_combo.addItem(language.name, language.locale)
        locale = current_locale or language_manager.current_locale
        index = self.language_combo.findData(locale)
        self.language_combo.setCurrentIndex(max(0, index))
        self.language_combo.blockSignals(False)

    def _emit_language_changed(self, _index: int) -> None:
        locale = self.language_combo.currentData()
        if locale:
            self.language_changed.emit(str(locale))

    def set_settings(self, settings: dict) -> None:
        index = self.start_page_combo.findData(settings.get("start_page", "home"))
        self.start_page_combo.setCurrentIndex(max(0, index))
        self.show_snapshots.setChecked(bool(settings.get("show_snapshots", False)))
        self.debug_mode.setChecked(bool(settings.get("debug_mode", False)))
        self.remember_window_size.setChecked(bool(settings.get("remember_window_size", True)))
        self.auto_check_updates.setChecked(bool(settings.get("auto_check_updates", True)))
        channel_index = self.update_channel_combo.findData(settings.get("update_channel", "beta"))
        self.update_channel_combo.setCurrentIndex(max(0, channel_index))
        self.reload_languages()
        language_index = self.language_combo.findData(settings.get("language", "en-US"))
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(max(0, language_index))
        self.language_combo.blockSignals(False)

    def form_data(self) -> dict:
        return {
            "start_page": self.start_page_combo.currentData(),
            "show_snapshots": self.show_snapshots.isChecked(),
            "debug_mode": self.debug_mode.isChecked(),
            "remember_window_size": self.remember_window_size.isChecked(),
            "language": self.language_combo.currentData() or "en-US",
            "auto_check_updates": self.auto_check_updates.isChecked(),
            "update_channel": self.update_channel_combo.currentData() or "beta",
        }

    def set_update_status(self, message: str) -> None:
        self.update_status_label.setText(message)

    def set_update_busy(self, busy: bool) -> None:
        self.check_updates_button.setEnabled(not busy)
