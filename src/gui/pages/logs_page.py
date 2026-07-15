from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit

from src.gui.pages.base_page import BasePage
from src.core.security.sensitive_data_redactor import SensitiveDataRedactor
from src.gui.widget.card_widget import CardWidget
from src.gui.theme.runtime import set_theme_icon


class LogsPage(BasePage):
    export_diagnostics_requested = Signal()
    open_logs_folder_requested = Signal()
    open_latest_game_log_requested = Signal()
    open_latest_crash_report_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Logs", "Frontend activity and structured progress events appear here.", "logs")
        self._build_ui()

    def _build_ui(self) -> None:
        card = CardWidget("Activity log")
        self.output = QTextEdit()
        self.output.setObjectName("LogOutput")
        self.output.setReadOnly(True)
        buttons = QHBoxLayout()
        copy_button = set_theme_icon(QPushButton("Copy all"), "icon.action.copy")
        clear_button = set_theme_icon(QPushButton("Clear"), "icon.action.clear")
        export_button = set_theme_icon(QPushButton("Export diagnostics"), "icon.action.export")
        open_folder_button = set_theme_icon(QPushButton("Open logs folder"), "icon.action.folder")
        open_game_log_button = set_theme_icon(QPushButton("Open latest game log"), "icon.action.folder")
        open_crash_report_button = set_theme_icon(QPushButton("Open latest crash report"), "icon.state.error")
        copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.output.toPlainText()))
        clear_button.clicked.connect(self.output.clear)
        export_button.clicked.connect(self.export_diagnostics_requested.emit)
        open_folder_button.clicked.connect(self.open_logs_folder_requested.emit)
        open_game_log_button.clicked.connect(self.open_latest_game_log_requested.emit)
        open_crash_report_button.clicked.connect(self.open_latest_crash_report_requested.emit)
        buttons.addWidget(copy_button)
        buttons.addWidget(clear_button)
        buttons.addStretch()
        buttons.addWidget(open_game_log_button)
        buttons.addWidget(open_crash_report_button)
        buttons.addWidget(open_folder_button)
        buttons.addWidget(export_button)
        card.layout.addWidget(self.output, 1)
        card.layout.addLayout(buttons)
        self.root_layout.addWidget(card, 1)

    def append(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.append(f"[{timestamp}] {SensitiveDataRedactor.redact_text(message)}")

    def activity_text(self) -> str:
        return self.output.toPlainText()
