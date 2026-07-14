from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit

from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class LogsPage(BasePage):
    export_diagnostics_requested = Signal()
    open_logs_folder_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Logs", "Frontend activity and structured progress events appear here.")
        self._build_ui()

    def _build_ui(self) -> None:
        card = CardWidget("Activity log")
        self.output = QTextEdit()
        self.output.setObjectName("LogOutput")
        self.output.setReadOnly(True)
        buttons = QHBoxLayout()
        copy_button = QPushButton("Copy all")
        clear_button = QPushButton("Clear")
        export_button = QPushButton("Export diagnostics")
        open_folder_button = QPushButton("Open logs folder")
        copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.output.toPlainText()))
        clear_button.clicked.connect(self.output.clear)
        export_button.clicked.connect(self.export_diagnostics_requested.emit)
        open_folder_button.clicked.connect(self.open_logs_folder_requested.emit)
        buttons.addWidget(copy_button)
        buttons.addWidget(clear_button)
        buttons.addStretch()
        buttons.addWidget(open_folder_button)
        buttons.addWidget(export_button)
        card.layout.addWidget(self.output, 1)
        card.layout.addLayout(buttons)
        self.root_layout.addWidget(card, 1)

    def append(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.append(f"[{timestamp}] {message}")

    def activity_text(self) -> str:
        return self.output.toPlainText()
