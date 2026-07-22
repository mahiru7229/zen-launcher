from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from src.gui.display_profile import fit_dialog_size


def resize_dialog_to_screen(widget: QWidget, preferred_width: int, preferred_height: int, minimum_width: int = 480, minimum_height: int = 320) -> tuple[int, int]:
    screen = widget.screen() or QGuiApplication.primaryScreen()
    if screen is None:
        width = max(int(minimum_width), int(preferred_width))
        height = max(int(minimum_height), int(preferred_height))
    else:
        available = screen.availableGeometry()
        width, height = fit_dialog_size(
            available.width(),
            available.height(),
            preferred_width,
            preferred_height,
            minimum_width,
            minimum_height,
        )

    widget.resize(width, height)
    return width, height
