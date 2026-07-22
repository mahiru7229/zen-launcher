from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout

from src.core.language.language_manager import tr
from src.gui.presenters.progress_presenter import ProgressPresenter
from src.gui.theme.runtime import set_theme_icon, set_theme_pixmap, set_theme_static_text


class LaunchControlWidget(QFrame):
    launch_clicked = Signal()

    LAUNCH_TEXT = "launch.button"
    CANCEL_TEXT = "launch.cancel_button"

    def __init__(self, compact: bool = False) -> None:
        super().__init__()
        self.setObjectName("LaunchControl")
        self._compact = bool(compact)
        self.setProperty("compactLayout", self._compact)
        self._mode = "idle"
        self._last_event: object | None = None
        self._last_result: dict | None = None
        self._last_error_status = "Launch failed"
        self._last_error_detail = "launch.error.logs_hint"
        self._last_exit_result: object | None = None
        self._busy = False
        self._launch_active = False
        self._pause_pending = False
        self._status_message = "Ready"
        self._detail_message = "Select an account and an instance, then launch."
        self._stage_state: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        if self._compact:
            layout.setContentsMargins(14, 9, 14, 9)
            layout.setSpacing(12)
        else:
            layout.setContentsMargins(20, 14, 20, 14)
            layout.setSpacing(18)

        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(10)

        stage_icon_size = 26 if self._compact else 32
        self.stage_icon = set_theme_pixmap(QLabel(), "icon.state.ready", stage_icon_size, stage_icon_size)

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

        self.launch_button = set_theme_icon(QPushButton(tr(self.LAUNCH_TEXT)), "icon.action.launch", 32 if self._compact else 40)
        set_theme_static_text(self.launch_button, "control.launch", tr(self.LAUNCH_TEXT))
        self.launch_button.setObjectName("PrimaryButton")
        self.launch_button.setProperty("themeRole", "launch")
        if self._compact:
            self.launch_button.setFixedSize(190, 60)
        else:
            self.launch_button.setFixedSize(230, 72)
        self.launch_button.clicked.connect(self.launch_clicked.emit)

        layout.addLayout(progress_layout, 1)
        layout.addWidget(self.launch_button)

    def set_selected_instance(self, _instance: object | None) -> None:
        self._refresh_launch_button()

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
        warnings = tuple(result.get("warnings", ()) or ())
        if warnings:
            self.status_label.setText(tr("Minecraft {version} launched with warnings", version=version))
            self.detail_label.setText(str(warnings[0]))
            self.stage_label.setText(tr("WARNING"))
            self._set_stage_state("warning")
        else:
            self.status_label.setText(tr("Minecraft {version} launched", version=version))
            self.detail_label.setText(tr("Java: {path}", path=java_path))
            self.stage_label.setText(tr("RUNNING"))
            self._set_stage_state("success")
        self._refresh_launch_button()


    def set_exit_result(self, result: object) -> None:
        self._mode = "exit"
        self._last_exit_result = result
        crashed = bool(getattr(result, "crashed", False))
        instance_name = str(getattr(result, "instance_name", "Minecraft"))
        exit_code = int(getattr(result, "exit_code", -1))
        duration_seconds = max(0, int(getattr(result, "duration_seconds", 0)))
        minutes, seconds = divmod(duration_seconds, 60)
        duration = tr("{minutes}m {seconds}s", minutes=minutes, seconds=seconds)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0 if crashed else 100)
        self.progress_bar.setFormat(tr("CRASHED") if crashed else tr("FINISHED"))
        if crashed:
            self.status_label.setText(tr("Minecraft crashed: {name}", name=instance_name))
            self.detail_label.setText(tr("Exit code: {code} • Play time: {duration}", code=exit_code, duration=duration))
            self.stage_label.setText(tr("CRASHED"))
            self._set_stage_state("error")
        else:
            self.status_label.setText(tr("Minecraft closed normally: {name}", name=instance_name))
            self.detail_label.setText(tr("Play time: {duration}", duration=duration))
            self.stage_label.setText(tr("FINISHED"))
            self._set_stage_state("success")
        self._refresh_launch_button()

    def set_failed(self, status: str = "Launch failed", detail: str | None = None) -> None:
        self._mode = "failed"
        self._last_error_status = status or "Launch failed"
        self._last_error_detail = detail or "launch.error.logs_hint"
        status_text = self._compact_failure_text(self._last_error_status, "Launch failed", 120)
        detail_text = self._compact_failure_text(self._last_error_detail, "launch.error.logs_hint", 180)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr("FAILED"))
        self.status_label.setText(status_text)
        self.detail_label.setText(detail_text)
        self.stage_label.setText(tr("FAILED"))
        self._set_stage_state("error")
        self._refresh_launch_button()

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
        self._refresh_launch_button()

    def set_launch_active(self, active: bool) -> None:
        self._launch_active = bool(active)
        if not self._launch_active:
            self._pause_pending = False
        self._refresh_launch_button()

    def set_pause_pending(self) -> None:
        if not self._launch_active:
            return
        self._pause_pending = True
        self.status_label.setText(tr("launch.pause_requested"))
        self.detail_label.setText(tr("launch.pause_requested_detail"))
        self.stage_label.setText(tr("launch.pausing_badge"))
        self._set_stage_state("warning")
        self._refresh_launch_button()

    def set_paused(self) -> None:
        self._mode = "paused"
        self._launch_active = False
        self._pause_pending = False
        self.status_label.setText(tr("launch.paused"))
        self.detail_label.setText(tr("launch.paused_detail"))
        self.stage_label.setText(tr("launch.paused_badge"))
        self.progress_bar.setFormat(tr("launch.paused_badge"))
        self._set_stage_state("warning")
        self._refresh_launch_button()

    def reset_progress(self) -> None:
        self._mode = "idle"
        self._busy = False
        self._launch_active = False
        self._pause_pending = False
        self._status_message = "Ready"
        self._detail_message = "Select an account and an instance, then launch."
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.status_label.setText(tr("Ready"))
        self.detail_label.setText(tr("Select an account and an instance, then launch."))
        self.stage_label.setText(tr("READY"))
        self._set_stage_state("success")
        self._refresh_launch_button()

    def _refresh_launch_button(self) -> None:
        is_cancel = self._launch_active
        text_key = self.CANCEL_TEXT if is_cancel else self.LAUNCH_TEXT
        static_role = "control.cancel" if is_cancel else "control.launch"
        theme_role = "cancel" if is_cancel else "launch"
        button_text = tr(text_key)

        self.launch_button.setProperty("themeRole", theme_role)
        self.launch_button.setProperty("themeStaticTextRole", static_role)
        self.launch_button.setProperty("themeStaticTextFallback", button_text)
        self.launch_button.setEnabled((is_cancel and not self._pause_pending) or (not is_cancel and not self._busy))

        if bool(self.launch_button.property("themeStaticTextHidden")):
            self.launch_button.setText("")
        elif self.launch_button.text() != button_text:
            self.launch_button.setText(button_text)

        self.launch_button.style().unpolish(self.launch_button)
        self.launch_button.style().polish(self.launch_button)

    def retranslate_dynamic(self) -> None:
        if self._mode == "progress" and self._last_event is not None:
            self.set_progress_event(self._last_event)
        elif self._mode == "result" and self._last_result is not None:
            self.set_result(self._last_result)
        elif self._mode == "failed":
            self.set_failed(self._last_error_status, self._last_error_detail)
        elif self._mode == "paused":
            self.set_paused()
        elif self._mode == "exit" and self._last_exit_result is not None:
            self.set_exit_result(self._last_exit_result)
        else:
            self.status_label.setText(tr(self._status_message))
            self.detail_label.setText(tr(self._detail_message))
            self.stage_label.setText(tr("READY"))
            self._refresh_launch_button()

    @staticmethod
    def _compact_failure_text(value: str, fallback: str, max_length: int) -> str:
        translated = tr(value or fallback)
        compact = " ".join(str(translated).split())
        if not compact or len(compact) > max_length:
            return tr(fallback)
        return compact

    def _set_stage_state(self, state: str) -> None:
        icon_state = "ready" if state == "success" and self._mode == "idle" else state
        state_key = f"{state}:{icon_state}"
        if self._stage_state == state_key:
            return
        self._stage_state = state_key
        set_theme_pixmap(self.stage_icon, f"icon.state.{icon_state}", 32, 32)
        self.stage_label.setProperty("state", state)
        self.stage_label.style().unpolish(self.stage_label)
        self.stage_label.style().polish(self.stage_label)
