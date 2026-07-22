from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class CardWidget(QFrame):
    def __init__(self, title: str, subtitle: str = "", object_name: str = "Card") -> None:
        super().__init__()
        self.setObjectName(object_name)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(10)
        self._compact = False

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            self.layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("CardSubtitle")
            subtitle_label.setWordWrap(True)
            self.layout.addWidget(subtitle_label)

    def set_compact_mode(self, compact: bool) -> None:
        self._compact = bool(compact)
        self.setProperty("compactLayout", self._compact)
        if self._compact:
            self.layout.setContentsMargins(12, 10, 12, 10)
            self.layout.setSpacing(7)
        else:
            self.layout.setContentsMargins(18, 16, 18, 16)
            self.layout.setSpacing(10)

