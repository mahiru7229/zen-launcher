from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from src.core.language.language_manager import tr
from src.models.update.update_info import UpdateInfo


class UpdateDialog(QDialog):
    UPDATE_NOW = "update"
    LATER = "later"
    DONT_ASK_AGAIN = "dont_ask_again"

    def __init__(self, info: UpdateInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.info = info
        self.decision = self.LATER
        self.setWindowTitle(tr("update.dialog.title"))
        self.setModal(True)
        self.resize(640, 500)

        layout = QVBoxLayout(self)
        title = QLabel(tr("update.dialog.heading", version=info.version))
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        message = QLabel(tr("update.dialog.message", current=info.current_version, version=info.version))
        message.setWordWrap(True)
        layout.addWidget(message)

        metadata = QLabel(tr("update.dialog.package_details", size=self._format_size(info.asset.size), asset=info.asset.name))
        metadata.setObjectName("ValueLabel")
        metadata.setWordWrap(True)
        layout.addWidget(metadata)

        notes_label = QLabel(tr("update.dialog.release_notes"))
        notes_label.setObjectName("CardTitle")
        layout.addWidget(notes_label)

        notes = QPlainTextEdit()
        notes.setReadOnly(True)
        notes.setPlainText(info.release_notes or tr("update.dialog.no_release_notes"))
        layout.addWidget(notes, 1)

        button_box = QDialogButtonBox()
        update_button = QPushButton(tr("update.dialog.update_now"))
        update_button.setObjectName("PrimaryButton")
        later_button = QPushButton(tr("update.dialog.later"))
        dont_ask_button = QPushButton(tr("update.dialog.dont_ask_again"))
        release_button = QPushButton(tr("update.dialog.open_release"))
        release_button.setEnabled(bool(info.release_url))
        button_box.addButton(update_button, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(later_button, QDialogButtonBox.ButtonRole.RejectRole)
        button_box.addButton(release_button, QDialogButtonBox.ButtonRole.ActionRole)
        button_box.addButton(dont_ask_button, QDialogButtonBox.ButtonRole.DestructiveRole)
        layout.addWidget(button_box)

        update_button.clicked.connect(lambda: self._finish(self.UPDATE_NOW, QDialog.DialogCode.Accepted))
        later_button.clicked.connect(lambda: self._finish(self.LATER, QDialog.DialogCode.Rejected))
        dont_ask_button.clicked.connect(lambda: self._finish(self.DONT_ASK_AGAIN, QDialog.DialogCode.Rejected))
        release_button.clicked.connect(self._open_release_page)

    def _open_release_page(self) -> None:
        if self.info.release_url:
            QDesktopServices.openUrl(QUrl(self.info.release_url))

    def _finish(self, decision: str, result: QDialog.DialogCode) -> None:
        self.decision = decision
        self.done(int(result))

    @staticmethod
    def _format_size(size: int) -> str:
        value = max(0, int(size))
        units = ("B", "KiB", "MiB", "GiB")
        amount = float(value)
        for unit in units:
            if amount < 1024 or unit == units[-1]:
                return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} {unit}"
            amount /= 1024
        return f"{value} B"

    @classmethod
    def ask(cls, info: UpdateInfo, parent: QWidget | None = None) -> str:
        dialog = cls(info, parent)
        dialog.exec()
        return dialog.decision
