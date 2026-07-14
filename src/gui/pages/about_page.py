from PySide6.QtWidgets import QLabel

from src.gui.config import DEVELOPER_NAME, LAUNCHER_NAME
from src.gui.pages.base_page import BasePage
from src.gui.widget.card_widget import CardWidget


class AboutPage(BasePage):
    def __init__(self) -> None:
        super().__init__("About", "Project information and the responsibilities of this GUI layer.")
        self._build_ui()

    def _build_ui(self) -> None:
        project_card = CardWidget(LAUNCHER_NAME, "A modular, open-source Minecraft launcher built with Python and PySide6.")
        developer = QLabel(f"Developer: {DEVELOPER_NAME}")
        developer.setObjectName("ValueLabel")
        license_label = QLabel("License: MIT")
        license_label.setObjectName("MutedLabel")
        project_card.layout.addWidget(developer)
        project_card.layout.addWidget(license_label)
        self.root_layout.addWidget(project_card)

        architecture_card = CardWidget("SRP architecture")
        architecture_text = QLabel(
            "• MainWindow assembles the shell and routes signals.\n"
            "• Pages own presentation and user input.\n"
            "• Controllers call only public Core APIs.\n"
            "• TaskRunner owns QThread lifecycle.\n"
            "• Reusable widgets own their own rendering state."
        )
        architecture_text.setWordWrap(True)
        architecture_card.layout.addWidget(architecture_text)
        self.root_layout.addWidget(architecture_card)

        asset_card = CardWidget("Assets", "No icon dependency is baked into the code. Buttons remain text-first until custom assets are added.")
        self.root_layout.addWidget(asset_card)
        self.root_layout.addStretch()
