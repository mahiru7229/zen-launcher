from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout

from src.core.instance.instance_manager import InstanceManager
from src.core.language.language_manager import tr
from src.gui.mod_instance_compatibility import CompatibleModVersion, normalize_supported_loader
from src.gui.window_sizing import resize_dialog_to_screen


class CreateCompatibleInstanceDialog(QDialog):
    def __init__(self, version: CompatibleModVersion, loader: str, parent=None) -> None:
        super().__init__(parent)
        self._version = version
        self._loader = normalize_supported_loader(loader)
        self._game_versions = tuple(dict.fromkeys(str(item).strip() for item in version.game_versions if str(item).strip()))
        if not self._game_versions:
            raise ValueError(tr("mods.instance_create.no_game_versions"))
        self._suggested_name = ""
        self._name_customized = False
        self._build_ui()
        self.retranslate_dynamic()
        self._update_suggested_name(force=True)

    @property
    def instance_name(self) -> str:
        return self.name_input.text().strip()

    @property
    def game_version(self) -> str:
        return str(self.game_version_combo.currentData() or self.game_version_combo.currentText()).strip()

    @property
    def loader(self) -> str:
        return self._loader

    def _build_ui(self) -> None:
        resize_dialog_to_screen(self, 520, 340, 460, 300)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PageTitle")
        root.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setObjectName("MutedLabel")
        self.description_label.setWordWrap(True)
        root.addWidget(self.description_label)

        self.name_label = QLabel()
        self.name_input = QLineEdit()
        self.name_input.textEdited.connect(self._mark_name_customized)
        root.addWidget(self.name_label)
        root.addWidget(self.name_input)

        self.game_version_label = QLabel()
        self.game_version_combo = QComboBox()
        for game_version in self._game_versions:
            self.game_version_combo.addItem(game_version, game_version)
        self.game_version_combo.currentIndexChanged.connect(lambda _index: self._update_suggested_name(force=False))
        root.addWidget(self.game_version_label)
        root.addWidget(self.game_version_combo)

        self.loader_label = QLabel()
        self.loader_value = QLabel()
        self.loader_value.setObjectName("ValueLabel")
        root.addWidget(self.loader_label)
        root.addWidget(self.loader_value)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.create_button = self.buttons.addButton(tr("mods.instance_create.create"), QDialogButtonBox.ButtonRole.AcceptRole)
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.clicked.connect(self._accept_create)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

    def _mark_name_customized(self, _text: str) -> None:
        self._name_customized = True

    def _update_suggested_name(self, force: bool) -> None:
        if self._name_customized and not force:
            return
        preferred = tr(
            "mods.instance_create.default_name",
            loader=self._loader.title(),
            version=self.game_version,
        )
        self._suggested_name = InstanceManager.next_available_name(preferred)
        self.name_input.setText(self._suggested_name)
        self._name_customized = False

    def _accept_create(self) -> None:
        try:
            name = InstanceManager.validate_name(self.instance_name)
        except Exception as error:
            QMessageBox.warning(self, tr("mods.instance_create.title"), str(error))
            return
        if InstanceManager.is_instance_exist(name):
            QMessageBox.warning(
                self,
                tr("mods.instance_create.title"),
                tr("mods.instance_create.name_exists", name=name),
            )
            return
        if not self.game_version:
            QMessageBox.warning(
                self,
                tr("mods.instance_create.title"),
                tr("mods.instance_create.select_version"),
            )
            return
        self.accept()

    def retranslate_dynamic(self) -> None:
        self.setWindowTitle(tr("mods.instance_create.title"))
        self.title_label.setText(tr("mods.instance_create.title"))
        self.description_label.setText(
            tr(
                "mods.instance_create.description",
                loader=self._loader.title(),
                mod_version=self._version.version_number,
            )
        )
        self.name_label.setText(tr("mods.instance_create.name"))
        self.game_version_label.setText(tr("mods.instance_create.minecraft"))
        self.loader_label.setText(tr("mods.instance_create.loader"))
        self.loader_value.setText(self._loader.title())
        self.create_button.setText(tr("mods.instance_create.create"))
