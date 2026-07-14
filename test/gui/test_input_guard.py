from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from src.gui.input_guard import ComboBoxWheelGuard


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_combo_box_wheel_event_is_blocked() -> None:
    app = _app()
    combo = QComboBox()
    guard = ComboBoxWheelGuard(app)

    assert guard.eventFilter(combo, QEvent(QEvent.Type.Wheel)) is True


def test_other_widget_wheel_event_is_not_blocked() -> None:
    app = _app()
    widget = QWidget()
    guard = ComboBoxWheelGuard(app)

    assert guard.eventFilter(widget, QEvent(QEvent.Type.Wheel)) is False
