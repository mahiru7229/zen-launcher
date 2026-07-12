from __future__ import annotations

import re
import sys
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from src.core.auth.offline_auth import OfflineAuthentication
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.models.account.account import Account
from src.models.account.account_source import AccountSource
from src.models.progress.progress_event import ProgressEvent


#THIS BUILD WAS CREATED BY CHATGPT 5.2


class TaskWorker(QObject):
    finished = Signal(object)
    failed = Signal(object)

    def __init__(self, task: Callable[[], Any]) -> None:
        super().__init__()
        self.task = task

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(self.task())
        except Exception as error:
            self.failed.emit(error)


class MainWindow(QMainWindow):
    progress_received = Signal(object)

    USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,16}$")
    INSTANCE_NAME_PATTERN = re.compile(r"^[^<>:\"/\\|?*\x00-\x1F]{1,80}$")

    def __init__(self) -> None:
        super().__init__()

        self._busy = False
        self._threads: list[QThread] = []
        self._manifest_versions: list[Any] = []

        self.setWindowTitle("MCW Launcher Beta")
        self.resize(1050, 680)
        self.setMinimumSize(920, 600)

        self._build_ui()
        self._apply_style()
        self.progress_received.connect(self._apply_progress_event)

        self._refresh_instances()
        self._run_task(self._load_manifest, "Loading Minecraft versions...", lock_ui=False, on_success=self._manifest_loaded)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content(), 1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(10)

        brand = QLabel("MCW")
        brand.setObjectName("Brand")

        caption = QLabel("Launcher Beta")
        caption.setObjectName("Muted")

        layout.addWidget(brand)
        layout.addWidget(caption)
        layout.addSpacing(18)

        self.nav_buttons: list[QPushButton] = []

        for index, text in enumerate(("Home", "Instances", "Activity Log")):
            button = QPushButton(text)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, page=index: self._switch_page(page))
            self.nav_buttons.append(button)
            layout.addWidget(button)

        self.nav_buttons[0].setChecked(True)
        layout.addStretch()

        footer = QLabel("MCW Core\nBeta 1")
        footer.setObjectName("Muted")
        layout.addWidget(footer)

        return sidebar

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("Content")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(18)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("MCW Launcher")
        title.setObjectName("PageTitle")
        subtitle = QLabel("A lightweight launcher powered by MCW Core.")
        subtitle.setObjectName("Muted")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.status_badge = QLabel("READY")
        self.status_badge.setObjectName("StatusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedWidth(110)

        header.addLayout(title_box, 1)
        header.addWidget(self.status_badge)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_home_page())
        self.pages.addWidget(self._build_instances_page())
        self.pages.addWidget(self._build_log_page())

        layout.addLayout(header)
        layout.addWidget(self.pages, 1)

        return content

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        grid = QGridLayout()
        grid.setHorizontalSpacing(15)

        account_card, account_layout = self._card("Offline account")
        self.username_input = QLineEdit("Steve")
        self.username_input.setPlaceholderText("Minecraft username")
        account_layout.addWidget(QLabel("Username"))
        account_layout.addWidget(self.username_input)

        version_card, version_layout = self._card("Minecraft version")
        self.version_combo = QComboBox()
        self.snapshot_checkbox = QCheckBox("Show snapshots")
        self.snapshot_checkbox.toggled.connect(self._apply_version_filter)

        refresh_versions = QPushButton("Refresh manifest")
        refresh_versions.clicked.connect(lambda: self._run_task(self._load_manifest, "Refreshing version manifest...", on_success=self._manifest_loaded))

        version_layout.addWidget(self.version_combo)
        version_layout.addWidget(self.snapshot_checkbox)
        version_layout.addWidget(refresh_versions)

        grid.addWidget(account_card, 0, 0)
        grid.addWidget(version_card, 0, 1)
        layout.addLayout(grid)

        launch_card, launch_layout = self._card("Quick launch")

        instance_row = QHBoxLayout()
        self.quick_instance_combo = QComboBox()

        refresh_instances = QPushButton("Refresh")
        refresh_instances.clicked.connect(self._refresh_instances)

        instance_row.addWidget(self.quick_instance_combo, 1)
        instance_row.addWidget(refresh_instances)

        self.launch_button = QPushButton("Launch Minecraft")
        self.launch_button.setObjectName("PrimaryButton")
        self.launch_button.setMinimumHeight(45)
        self.launch_button.clicked.connect(self.launch_selected_instance)

        launch_layout.addLayout(instance_row)
        launch_layout.addWidget(self.launch_button)
        layout.addWidget(launch_card)

        progress_card, progress_layout = self._card("Launch progress")
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusText")
        self.progress_detail = QLabel("No task running")
        self.progress_detail.setObjectName("Muted")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_detail)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_card)
        layout.addStretch()

        return page

    def _build_instances_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        card, card_layout = self._card("Instance manager")

        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self._instance_selected)

        self.instance_name_input = QLineEdit()
        self.instance_name_input.setPlaceholderText("Instance name / new name / clone name")

        card_layout.addWidget(QLabel("Selected instance"))
        card_layout.addWidget(self.instance_combo)
        card_layout.addWidget(QLabel("Target name"))
        card_layout.addWidget(self.instance_name_input)

        grid = QGridLayout()
        self.create_button = QPushButton("Create")
        self.rename_button = QPushButton("Rename")
        self.clone_button = QPushButton("Clone")
        self.delete_button = QPushButton("Delete")
        self.import_button = QPushButton("Import .mcwpack")
        self.export_button = QPushButton("Export .mcwpack")

        self.delete_button.setObjectName("DangerButton")

        self.create_button.clicked.connect(self.create_instance)
        self.rename_button.clicked.connect(self.rename_instance)
        self.clone_button.clicked.connect(self.clone_instance)
        self.delete_button.clicked.connect(self.delete_instance)
        self.import_button.clicked.connect(self.import_instance)
        self.export_button.clicked.connect(self.export_instance)

        grid.addWidget(self.create_button, 0, 0)
        grid.addWidget(self.rename_button, 0, 1)
        grid.addWidget(self.clone_button, 0, 2)
        grid.addWidget(self.delete_button, 0, 3)
        grid.addWidget(self.import_button, 1, 0, 1, 2)
        grid.addWidget(self.export_button, 1, 2, 1, 2)

        self.include_saves_checkbox = QCheckBox("Include saves when cloning or exporting")

        card_layout.addLayout(grid)
        card_layout.addWidget(self.include_saves_checkbox)

        layout.addWidget(card)
        layout.addStretch()

        return page

    def _build_log_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        card, card_layout = self._card("Activity log")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setObjectName("LogOutput")

        clear_button = QPushButton("Clear log")
        clear_button.clicked.connect(self.log_output.clear)

        card_layout.addWidget(self.log_output, 1)
        card_layout.addWidget(clear_button)
        layout.addWidget(card, 1)

        return page

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("Card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        layout.addWidget(title_label)

        return frame, layout

    def _switch_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)

        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def _run_task(self, task: Callable[[], Any], message: str, lock_ui: bool = True, on_success: Callable[[Any], None] | None = None) -> None:
        if lock_ui and self._busy:
            QMessageBox.information(self, "Task running", "Wait for the current task to finish.")
            return

        if lock_ui:
            self._set_busy(True)

        self._set_status(message)
        self._append_log(message)

        thread = QThread(self)
        worker = TaskWorker(task)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(lambda result: self._task_finished(thread, worker, result, on_success, lock_ui))
        worker.failed.connect(lambda error: self._task_failed(thread, worker, error, lock_ui))

        self._threads.append(thread)
        thread.start()

    def _task_finished(self, thread: QThread, worker: TaskWorker, result: Any, on_success: Callable[[Any], None] | None, lock_ui: bool) -> None:
        if on_success is not None:
            on_success(result)

        if lock_ui:
            self._set_busy(False)

        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()

        if thread in self._threads:
            self._threads.remove(thread)

    def _task_failed(self, thread: QThread, worker: TaskWorker, error: Exception, lock_ui: bool) -> None:
        if lock_ui:
            self._set_busy(False)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        message = f"{type(error).__name__}: {error}"
        self._set_status("Task failed")
        self._append_log(message)
        QMessageBox.critical(self, "MCW Launcher", message)

        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()

        if thread in self._threads:
            self._threads.remove(thread)

    def _load_manifest(self) -> list[Any]:
        versions = VersionManifestManager.get()

        if not versions:
            raise RuntimeError("Minecraft version manifest is unavailable.")

        return versions

    def _manifest_loaded(self, versions: list[Any]) -> None:
        self._manifest_versions = versions
        self._apply_version_filter()
        self._set_status(f"Loaded {len(versions)} Minecraft versions")

    def _apply_version_filter(self) -> None:
        selected = self.version_combo.currentText()
        include_snapshots = self.snapshot_checkbox.isChecked()

        version_ids = [
            version.id
            for version in self._manifest_versions
            if version.type == "release" or include_snapshots
        ]

        self.version_combo.clear()
        self.version_combo.addItems(version_ids)

        if selected in version_ids:
            self.version_combo.setCurrentText(selected)

    def _refresh_instances(self) -> None:
        try:
            names = sorted(instance.name for instance in InstanceManager.list_instances())
        except Exception as error:
            QMessageBox.critical(self, "MCW Launcher", f"{type(error).__name__}: {error}")
            return

        selected = self.instance_combo.currentText() or self.quick_instance_combo.currentText()

        self.instance_combo.blockSignals(True)
        self.quick_instance_combo.blockSignals(True)

        self.instance_combo.clear()
        self.quick_instance_combo.clear()
        self.instance_combo.addItems(names)
        self.quick_instance_combo.addItems(names)

        if selected in names:
            self.instance_combo.setCurrentText(selected)
            self.quick_instance_combo.setCurrentText(selected)

        self.instance_combo.blockSignals(False)
        self.quick_instance_combo.blockSignals(False)

        if self.instance_combo.currentText():
            self._instance_selected(self.instance_combo.currentText())

        self._append_log(f"Instances refreshed: {len(names)} found")

    def _instance_selected(self, name: str) -> None:
        if not name:
            return

        try:
            instance = InstanceManager.load(name)
        except Exception as error:
            self._append_log(f"{type(error).__name__}: {error}")
            return

        self.instance_name_input.setText(instance.name)
        self.version_combo.setCurrentText(getattr(instance, "version_id", ""))

        if self.quick_instance_combo.currentText() != name:
            self.quick_instance_combo.setCurrentText(name)

    def create_instance(self) -> None:
        name = self._validated_instance_name()
        version_id = self.version_combo.currentText().strip()

        if name is None or not version_id:
            return

        def task() -> Any:
            return InstanceManager.create(name=name, version=VersionManager.load(version_id))

        self._run_task(task, f"Creating '{name}'...", on_success=lambda instance: self._instance_action_finished(instance.name, f"Created '{instance.name}'"))

    def rename_instance(self) -> None:
        source = self.instance_combo.currentText().strip()
        target = self._validated_instance_name()

        if not source or target is None:
            return

        def task() -> Path:
            return InstanceManager.rename(source, target)

        self._run_task(task, f"Renaming '{source}'...", on_success=lambda _path: self._instance_action_finished(target, f"Renamed '{source}' to '{target}'"))

    def clone_instance(self) -> None:
        source = self.instance_combo.currentText().strip()
        target = self._validated_instance_name()

        if not source or target is None:
            return

        include_saves = self.include_saves_checkbox.isChecked()

        def task() -> Any:
            return InstanceManager.clone(source_name=source, new_name=target, include_saves=include_saves)

        self._run_task(task, f"Cloning '{source}'...", on_success=lambda instance: self._instance_action_finished(instance.name, f"Cloned '{source}' to '{instance.name}'"))

    def delete_instance(self) -> None:
        name = self.instance_combo.currentText().strip()

        if not name:
            return

        answer = QMessageBox.question(self, "Delete instance", f"Delete '{name}' and its entire folder?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._run_task(lambda: InstanceManager.delete_instance(name), f"Deleting '{name}'...", on_success=lambda _deleted: self._instance_action_finished("", f"Deleted '{name}'"))

    def import_instance(self) -> None:
        package_path, _ = QFileDialog.getOpenFileName(self, "Import MCW instance", "", "MCW Package (*.mcwpack *.zip)")

        if not package_path:
            return

        self._run_task(lambda: InstanceManager.import_instance(Path(package_path)), f"Importing '{Path(package_path).name}'...", on_success=lambda instance: self._instance_action_finished(instance.name, f"Imported '{instance.name}'"))

    def export_instance(self) -> None:
        name = self.instance_combo.currentText().strip()

        if not name:
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Export MCW instance", f"{name}.mcwpack", "MCW Package (*.mcwpack)")

        if not output_path:
            return

        include_saves = self.include_saves_checkbox.isChecked()

        def task() -> Path:
            return InstanceManager.export(instance_name=name, output_path=Path(output_path), include_saves=include_saves)

        self._run_task(task, f"Exporting '{name}'...", on_success=lambda path: QMessageBox.information(self, "Export complete", f"Saved to:\n{path}"))

    def _instance_action_finished(self, selected_name: str, status: str) -> None:
        self._refresh_instances()

        if selected_name:
            self.instance_combo.setCurrentText(selected_name)
            self.quick_instance_combo.setCurrentText(selected_name)

        self._set_status(status)

    def launch_selected_instance(self) -> None:
        instance_name = self.quick_instance_combo.currentText().strip()
        username = self.username_input.text().strip()

        if not instance_name:
            QMessageBox.warning(self, "Instance", "Select an instance first.")
            return

        if not self.USERNAME_PATTERN.fullmatch(username):
            QMessageBox.warning(self, "Username", "Username must contain 3-16 letters, numbers, or underscores.")
            return

        def task() -> dict:
            instance = InstanceManager.load(instance_name)
            account = Account(account_id=str(uuid.uuid4()), account_type=AccountSource.OFFLINE, username=username, uuid=OfflineAuthentication.uuid_generator(username))
            authentication = OfflineAuthentication.authenticate(account)
            return MinecraftExecutor.run(instance=instance, authentication=authentication, account=account, on_progress=self._on_progress)

        def success(info: dict) -> None:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self._set_status(f"Minecraft {info.get('minecraftVersion', 'unknown')} launched")
            self.progress_detail.setText(f"Java: {info.get('javaPath', 'unknown')}")

        self._run_task(task, f"Launching '{instance_name}'...", on_success=success)

    def _on_progress(self, event: ProgressEvent) -> None:
        self.progress_received.emit(event)

    @Slot(object)
    def _apply_progress_event(self, event: ProgressEvent) -> None:
        self.status_label.setText(event.message)
        self.status_badge.setText(event.stage.value.replace("_", " ").upper())

        if event.is_determinate:
            percentage = event.percentage or 0
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(percentage))
            self.progress_detail.setText(f"{event.current}/{event.total} ({percentage:.1f}%)")
        else:
            self.progress_bar.setRange(0, 0)
            self.progress_detail.setText(event.stage.value.replace("_", " ").title())

        self._append_log(self._format_progress(event))

    @staticmethod
    def _format_progress(event: ProgressEvent) -> str:
        if event.is_determinate:
            return f"[{event.stage.value}] {event.message} {event.current}/{event.total} ({event.percentage or 0:.1f}%)"

        return f"[{event.stage.value}] {event.message}"

    def _validated_instance_name(self) -> str | None:
        name = self.instance_name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Instance name", "Enter an instance name.")
            return None

        if name in {".", ".."} or not self.INSTANCE_NAME_PATTERN.fullmatch(name) or name.endswith((" ", ".")):
            QMessageBox.warning(self, "Instance name", "The instance name is not valid on Windows.")
            return None

        return name

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy

        for widget in (self.launch_button, self.create_button, self.rename_button, self.clone_button, self.delete_button, self.import_button, self.export_button):
            widget.setEnabled(not busy)

        self.status_badge.setText("BUSY" if busy else "READY")

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

        if not self._busy:
            self.status_badge.setText("READY")

    def _append_log(self, message: str) -> None:
        self.log_output.append(message)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget#Root { background: #11151c; color: #f1f4f8; font-family: "Segoe UI"; font-size: 10pt; }
            QFrame#Sidebar { background: #0b0e13; border-right: 1px solid #252c37; }
            QWidget#Content { background: #11151c; }
            QLabel#Brand { color: #8ce58b; font-size: 30px; font-weight: 800; }
            QLabel#PageTitle { font-size: 25px; font-weight: 700; }
            QLabel#Muted { color: #8f99aa; }
            QLabel#CardTitle { font-size: 15px; font-weight: 700; }
            QLabel#StatusText { font-size: 14px; font-weight: 600; }
            QLabel#StatusBadge { background: #203a2a; color: #9cf3a1; border: 1px solid #396348; border-radius: 9px; padding: 7px; font-weight: 700; }
            QFrame#Card { background: #191e27; border: 1px solid #2a323f; border-radius: 12px; }
            QPushButton { background: #29313d; border: 1px solid #3a4555; border-radius: 8px; padding: 9px 13px; font-weight: 600; }
            QPushButton:hover { background: #354050; }
            QPushButton:pressed { background: #222a34; }
            QPushButton:disabled { color: #69717e; background: #20252e; }
            QPushButton#PrimaryButton { background: #4c9f5b; border-color: #68bf75; }
            QPushButton#PrimaryButton:hover { background: #5ab168; }
            QPushButton#DangerButton { background: #4b252a; border-color: #764049; }
            QPushButton#NavButton { text-align: left; background: transparent; border: none; color: #b8bfca; }
            QPushButton#NavButton:hover { background: #181d26; }
            QPushButton#NavButton:checked { background: #203126; color: #9cf3a1; }
            QLineEdit, QComboBox, QTextEdit { background: #0f131a; border: 1px solid #303a48; border-radius: 8px; padding: 8px 10px; selection-background-color: #43814f; }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border-color: #6ccf77; }
            QProgressBar { background: #0f131a; border: 1px solid #303a48; border-radius: 7px; min-height: 14px; }
            QProgressBar::chunk { background: #62c96f; border-radius: 6px; }
            QTextEdit#LogOutput { font-family: Consolas; font-size: 10pt; }
            QScrollBar:vertical { background: #0f131a; width: 12px; }
            QScrollBar::handle:vertical { background: #3a4554; min-height: 30px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MCW Launcher")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()