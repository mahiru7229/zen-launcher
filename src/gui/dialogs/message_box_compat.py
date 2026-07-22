from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox


MESSAGE_BOX_STYLE = """
QMessageBox {
    background-color: #f2f3ef;
    color: #171817;
}

QMessageBox QLabel {
    background: transparent;
    color: #171817;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}

QMessageBox QPushButton {
    min-width: 88px;
    background: #dfe3da;
    color: #171817;
    border: 2px solid #747a6e;
    padding: 7px 12px;
    font-weight: 700;
}

QMessageBox QPushButton:hover {
    background: #cbd7bf;
    color: #10120e;
}

QMessageBox QPushButton:pressed {
    background: #b9c7ac;
}
"""


def apply_message_box_compatibility(message_box: QMessageBox) -> None:
    message_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    palette = QPalette(message_box.palette())
    background = QColor("#f2f3ef")
    foreground = QColor("#171817")
    button = QColor("#dfe3da")
    palette.setColor(QPalette.ColorRole.Window, background)
    palette.setColor(QPalette.ColorRole.Base, background)
    palette.setColor(QPalette.ColorRole.AlternateBase, background)
    palette.setColor(QPalette.ColorRole.WindowText, foreground)
    palette.setColor(QPalette.ColorRole.Text, foreground)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, foreground)
    message_box.setPalette(palette)
    message_box.setStyleSheet(MESSAGE_BOX_STYLE)


class MessageBoxCompatibilityFilter(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Show and isinstance(watched, QMessageBox):
            apply_message_box_compatibility(watched)
        return super().eventFilter(watched, event)


def install_message_box_compatibility(application: QApplication) -> MessageBoxCompatibilityFilter:
    compatibility_filter = MessageBoxCompatibilityFilter(application)
    application.installEventFilter(compatibility_filter)
    return compatibility_filter
