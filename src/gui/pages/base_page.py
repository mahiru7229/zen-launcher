from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from src.gui.widget.card_widget import CardWidget


class BasePage(QScrollArea):
    def __init__(self, title: str, subtitle: str, page_id: str = "generic") -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        page = QWidget()
        page.setObjectName("PageViewport")
        page.setProperty("themePage", str(page_id))
        self.setWidget(page)
        self.page_viewport = page
        self.root_layout = QVBoxLayout(page)
        self.root_layout.setContentsMargins(28, 24, 28, 24)
        self.root_layout.setSpacing(18)
        self._compact = False

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)
        self.root_layout.addWidget(title_label)
        self.root_layout.addWidget(subtitle_label)

    def set_compact_mode(self, compact: bool) -> None:
        self._compact = bool(compact)
        self.page_viewport.setProperty("compactLayout", self._compact)
        if self._compact:
            self.root_layout.setContentsMargins(18, 14, 18, 14)
            self.root_layout.setSpacing(12)
        else:
            self.root_layout.setContentsMargins(28, 24, 28, 24)
            self.root_layout.setSpacing(18)

        for card in self.findChildren(CardWidget):
            card.set_compact_mode(self._compact)

