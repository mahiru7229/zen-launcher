from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout


class LaunchControlWidget(QFrame):
    launch_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LaunchControl")
        self._selected_instance = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(18)

        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("ValueLabel")
        self.detail_label = QLabel("Select an account and an instance, then launch.")
        self.detail_label.setObjectName("TinyLabel")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.status_label)
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
        self.launch_button.setText(f"LAUNCH\n{self._selected_instance}" if self._selected_instance else "LAUNCH")

    def set_status(self, message: str, detail: str | None = None) -> None:
        self.status_label.setText(message)
        if detail is not None:
            self.detail_label.setText(detail)

    def set_progress_event(self, event: object) -> None:
        self.status_label.setText(getattr(event, "message", "Working..."))
        stage = getattr(getattr(event, "stage", None), "value", "working").replace("_", " ").title()
        if getattr(event, "is_determinate", False):
            percentage = float(getattr(event, "percentage", 0) or 0)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(percentage))
            current = getattr(event, "current", 0)
            total = getattr(event, "total", 0)
            unit = getattr(event, "unit", "") or ""
            self.detail_label.setText(f"{stage} — {current}/{total} {unit} ({percentage:.1f}%)")
        else:
            self.progress_bar.setRange(0, 0)
            self.detail_label.setText(stage)

    def set_result(self, result: dict) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Minecraft {result.get('minecraftVersion', 'unknown')} launched")
        self.detail_label.setText(f"Java: {result.get('javaPath', 'unknown')}")

    def set_busy(self, busy: bool) -> None:
        self.launch_button.setEnabled(not busy)
        if busy:
            self.launch_button.setText("WORKING...")
        else:
            self.launch_button.setText(f"LAUNCH\n{self._selected_instance}" if self._selected_instance else "LAUNCH")

    def reset_progress(self) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
