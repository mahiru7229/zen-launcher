from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from src.core.language.language_manager import tr
from src.gui.presenters.progress_presenter import ProgressPresenter
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap


class LaunchControlWidget(QFrame):
    launch_clicked = Signal()

    BUTTON_TEXT = "Launch"

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LaunchControl")
        self._mode = "idle"
        self._last_event: object | None = None
        self._last_result: dict | None = None
        self._last_error = ""
        self._status_message = "Ready"
        self._detail_message = "Select an account and an instance, then launch."
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(18)

        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(10)

        self.stage_icon = set_theme_pixmap(QLabel(), "icon.state.ready", 32, 32)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("ValueLabel")

        self.stage_label = QLabel("READY")
        self.stage_label.setObjectName("StageBadge")
        self.stage_label.setProperty("state", "success")

        status_row.addWidget(self.stage_icon)
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.stage_label)

        self.detail_label = QLabel("Select an account and an instance, then launch.")
        self.detail_label.setObjectName("TinyLabel")
        self.detail_label.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")

        progress_layout.addLayout(status_row)
        progress_layout.addWidget(self.detail_label)
        progress_layout.addWidget(self.progress_bar)

        self.launch_button = set_theme_icon(QPushButton(self.BUTTON_TEXT), "icon.action.launch", 40)
        self.launch_button.setObjectName("PrimaryButton")
        self.launch_button.setProperty("themeRole", "launch")
        self.launch_button.setFixedSize(230, 72)
        self.launch_button.clicked.connect(self.launch_clicked.emit)

        layout.addLayout(progress_layout, 1)
        layout.addWidget(self.launch_button)

    def set_selected_instance(self, _instance: object | None) -> None:
        self._keep_launch_button_text()

    def set_status(self, message: str, detail: str | None = None) -> None:
        self._status_message = message
        self.status_label.setText(tr(message))

        if detail is not None:
            self._detail_message = detail
            self.detail_label.setText(tr(detail))

    def set_progress_event(self, event: object) -> None:
        self._mode = "progress"
        self._last_event = event
        view = ProgressPresenter.present(event)

        self.status_label.setText(view.title)
        self.detail_label.setText(view.detail)
        self.stage_label.setText(view.stage_text)
        self._set_stage_state("busy")
        self._keep_launch_button_text()

        if view.percentage is None:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("")
            return

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(view.percentage)
        self.progress_bar.setFormat(f"{view.percentage}%")

    def set_result(self, result: dict) -> None:
        self._mode = "result"
        self._last_result = dict(result)
        version = result.get("minecraftVersion", "unknown")
        java_path = result.get("javaPath", "unknown")

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100%")
        self.status_label.setText(tr("Minecraft {version} launched", version=version))
        self.detail_label.setText(tr("Java: {path}", path=java_path))
        self.stage_label.setText(tr("RUNNING"))
        self._set_stage_state("success")
        self._keep_launch_button_text()

    def set_failed(self, message: str) -> None:
        self._mode = "failed"
        self._last_error = message
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr("FAILED"))
        self.status_label.setText(tr("Launch failed"))
        self.detail_label.setText(message or tr("Minecraft could not be started."))
        self.stage_label.setText(tr("FAILED"))
        self._set_stage_state("error")
        self._keep_launch_button_text()

    def set_busy(self, busy: bool) -> None:
        self.launch_button.setEnabled(not busy)
        self._keep_launch_button_text()

    def reset_progress(self) -> None:
        self._mode = "idle"
        self._status_message = "Ready"
        self._detail_message = "Select an account and an instance, then launch."
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.status_label.setText(tr("Ready"))
        self.detail_label.setText(tr("Select an account and an instance, then launch."))
        self.stage_label.setText(tr("READY"))
        self._set_stage_state("success")
        self._keep_launch_button_text()

    def _keep_launch_button_text(self) -> None:
        if self.launch_button.text() != self.BUTTON_TEXT:
            self.launch_button.setText(self.BUTTON_TEXT)

    def retranslate_dynamic(self) -> None:
        if self._mode == "progress" and self._last_event is not None:
            self.set_progress_event(self._last_event)
        elif self._mode == "result" and self._last_result is not None:
            self.set_result(self._last_result)
        elif self._mode == "failed":
            self.set_failed(self._last_error)
        else:
            self.status_label.setText(tr(self._status_message))
            self.detail_label.setText(tr(self._detail_message))
            self.stage_label.setText(tr("READY"))
            self._keep_launch_button_text()

    def _set_stage_state(self, state: str) -> None:
        icon_state = "ready" if state == "success" and self._mode == "idle" else state
        set_theme_pixmap(self.stage_icon, f"icon.state.{icon_state}", 32, 32)
        self.stage_label.setProperty("state", state)
        self.stage_label.style().unpolish(self.stage_label)
        self.stage_label.style().polish(self.stage_label)
