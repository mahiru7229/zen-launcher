from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from src.gui.presenters.progress_presenter import ProgressPresenter
from src.gui.widget.launch_control_style import LAUNCH_CONTROL_STYLE


class LaunchControlWidget(QFrame):
    launch_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LaunchControl")

        self._selected_instance = ""
        self._busy = False
        self._busy_button_text = "WORKING..."

        self._build_ui()
        self.setStyleSheet(LAUNCH_CONTROL_STYLE)

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

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("ValueLabel")

        self.stage_label = QLabel("READY")
        self.stage_label.setObjectName("StageBadge")
        self.stage_label.setProperty("state", "success")

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

        self.launch_button = QPushButton("LAUNCH")
        self.launch_button.setObjectName("PrimaryButton")
        self.launch_button.setFixedSize(230, 72)
        self.launch_button.clicked.connect(self.launch_clicked.emit)

        layout.addLayout(progress_layout, 1)
        layout.addWidget(self.launch_button)

    def set_selected_instance(self, instance: object | None) -> None:
        self._selected_instance = getattr(instance, "name", "") if instance is not None else ""
        self._refresh_launch_button()

    def set_status(self, message: str, detail: str | None = None) -> None:
        self.status_label.setText(message)

        if detail is not None:
            self.detail_label.setText(detail)

    def set_progress_event(self, event: object) -> None:
        view = ProgressPresenter.present(event)

        self.status_label.setText(view.title)
        self.detail_label.setText(view.detail)
        self.stage_label.setText(view.stage_text)
        self._set_stage_state("busy")

        self._busy_button_text = view.button_text
        self._refresh_launch_button()

        if view.percentage is None:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("")
            return

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(view.percentage)
        self.progress_bar.setFormat(f"{view.percentage}%")

    def set_result(self, result: dict) -> None:
        version = result.get("minecraftVersion", "unknown")
        java_path = result.get("javaPath", "unknown")

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100%")
        self.status_label.setText(f"Minecraft {version} launched")
        self.detail_label.setText(f"Java: {java_path}")
        self.stage_label.setText("RUNNING")
        self._set_stage_state("success")

    def set_failed(self, message: str) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("FAILED")
        self.status_label.setText("Launch failed")
        self.detail_label.setText(message or "Minecraft could not be started.")
        self.stage_label.setText("FAILED")
        self._set_stage_state("error")

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.launch_button.setEnabled(not busy)
        self._refresh_launch_button()

    def reset_progress(self) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.status_label.setText("Ready")
        self.detail_label.setText("Select an account and an instance, then launch.")
        self.stage_label.setText("READY")
        self._set_stage_state("success")

    def _refresh_launch_button(self) -> None:
        if self._busy:
            self.launch_button.setText(self._busy_button_text)
            return

        if self._selected_instance:
            self.launch_button.setText(f"LAUNCH\n{self._selected_instance}")
            return

        self.launch_button.setText("LAUNCH")

    def _set_stage_state(self, state: str) -> None:
        self.stage_label.setProperty("state", state)
        self.stage_label.style().unpolish(self.stage_label)
        self.stage_label.style().polish(self.stage_label)
