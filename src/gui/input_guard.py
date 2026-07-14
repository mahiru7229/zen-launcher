from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QComboBox


class ComboBoxWheelGuard(QObject):
    """Prevent mouse-wheel changes on closed combo boxes.

    The popup view remains scrollable because wheel events inside the opened
    list are delivered to its viewport, not to the QComboBox itself.
    """

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and isinstance(watched, QComboBox):
            event.accept()
            return True
        return super().eventFilter(watched, event)


def install_combo_box_wheel_guard(app: QApplication) -> ComboBoxWheelGuard:
    guard = ComboBoxWheelGuard(app)
    app.installEventFilter(guard)
    return guard
