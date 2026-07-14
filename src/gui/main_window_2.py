from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from src.gui.config import LAUNCHER_NAME, MINIMUM_HEIGHT, MINIMUM_WIDTH, RIGHT_PANEL_WIDTH, SIDEBAR_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH
from src.gui.controllers.account_controller import AccountController
from src.gui.controllers.gui_settings_controller import GuiSettingsController
from src.gui.controllers.instance_controller import InstanceController
from src.gui.controllers.launch_controller import LaunchController
from src.gui.controllers.settings_controller import InstanceSettingsController
from src.gui.controllers.version_controller import VersionController
from src.gui.pages.about_page import AboutPage
from src.gui.pages.account_page import AccountPage
from src.gui.pages.home_page import HomePage
from src.gui.pages.instance_settings_page import InstanceSettingsPage
from src.gui.pages.instances_page import InstancesPage
from src.gui.pages.launcher_settings_page import LauncherSettingsPage
from src.gui.pages.logs_page import LogsPage
from src.gui.style import APP_STYLE
from src.gui.task_runner import TaskRunner
from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.gui.widget.right_panel_widget import RightPanelWidget
from src.gui.widget.sidebar_widget import SidebarWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(LAUNCHER_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MINIMUM_WIDTH, MINIMUM_HEIGHT)

        self.task_runner = TaskRunner(self)
        self.version_controller = VersionController(self.task_runner)
        self.account_controller = AccountController()
        self.instance_controller = InstanceController(self.task_runner)
        self.instance_settings_controller = InstanceSettingsController()
        self.gui_settings_controller = GuiSettingsController()
        self.launch_controller = LaunchController(self.task_runner)

        self._build_ui()
        self._connect_signals()
        self.setStyleSheet(APP_STYLE)
        self._initialize_data()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = SidebarWidget()
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)

        center = QWidget()
        center.setObjectName("CenterArea")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        self.launch_control = LaunchControlWidget()
        center_layout.addWidget(self.content_stack, 1)
        center_layout.addWidget(self.launch_control)

        self.right_panel = RightPanelWidget()
        self.right_panel.setFixedWidth(RIGHT_PANEL_WIDTH)

        self.home_page = HomePage()
        self.account_page = AccountPage()
        self.instances_page = InstancesPage()
        self.instance_settings_page = InstanceSettingsPage()
        self.launcher_settings_page = LauncherSettingsPage()
        self.logs_page = LogsPage()
        self.about_page = AboutPage()

        self.pages = {
            "home": self.home_page,
            "accounts": self.account_page,
            "instances": self.instances_page,
            "instance_settings": self.instance_settings_page,
            "launcher_settings": self.launcher_settings_page,
            "logs": self.logs_page,
            "about": self.about_page,
        }
        for page in self.pages.values():
            self.content_stack.addWidget(page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(center, 1)
        root_layout.addWidget(self.right_panel)

    def _connect_signals(self) -> None:
        self.sidebar.page_requested.connect(self.show_page)
        self.home_page.manage_accounts_requested.connect(lambda: self.show_page("accounts"))
        self.home_page.manage_instances_requested.connect(lambda: self.show_page("instances"))
        self.home_page.open_settings_requested.connect(lambda: self.show_page("launcher_settings"))
        self.right_panel.manage_accounts_requested.connect(lambda: self.show_page("accounts"))
        self.right_panel.manage_instances_requested.connect(lambda: self.show_page("instances"))
        self.right_panel.refresh_requested.connect(self._refresh_all)

        self.account_page.create_offline_requested.connect(self.account_controller.create_offline)
        self.account_page.select_requested.connect(self.account_controller.select)
        self.account_page.remove_requested.connect(self.account_controller.remove)
        self.account_page.refresh_requested.connect(self.account_controller.refresh)

        self.instances_page.refresh_requested.connect(self.instance_controller.refresh)
        self.instances_page.selected_instance_changed.connect(self.instance_controller.select)
        self.instances_page.create_requested.connect(self.instance_controller.create)
        self.instances_page.rename_requested.connect(self.instance_controller.rename)
        self.instances_page.clone_requested.connect(self.instance_controller.clone)
        self.instances_page.delete_requested.connect(self.instance_controller.delete)
        self.instances_page.import_requested.connect(self.instance_controller.import_package)
        self.instances_page.export_requested.connect(self.instance_controller.export_package)

        self.instance_settings_page.load_requested.connect(self.instance_settings_controller.load)
        self.instance_settings_page.save_requested.connect(self.instance_settings_controller.save)
        self.launcher_settings_page.save_requested.connect(self.gui_settings_controller.save)
        self.launcher_settings_page.reset_requested.connect(self.gui_settings_controller.reset)
        self.launch_control.launch_clicked.connect(self.launch_controller.launch)

        self.version_controller.versions_changed.connect(self.instances_page.set_versions)
        self.version_controller.versions_changed.connect(lambda versions: self.home_page.set_manifest_count(len(versions)))
        self.account_controller.accounts_changed.connect(self.account_page.set_accounts)
        self.account_controller.selected_account_changed.connect(self._account_selected)
        self.instance_controller.instances_changed.connect(self.instances_page.set_instances)
        self.instance_controller.instances_changed.connect(self.instance_settings_page.set_instances)
        self.instance_controller.selected_instance_changed.connect(self._instance_selected)
        self.instance_controller.export_finished.connect(self._show_export_finished)
        self.instance_settings_controller.settings_loaded.connect(self.instance_settings_page.set_settings)
        self.gui_settings_controller.settings_changed.connect(self._apply_gui_settings)
        self.launch_controller.progress_received.connect(self._on_progress)
        self.launch_controller.launch_finished.connect(self.launch_control.set_result)

        self.task_runner.task_started.connect(self._on_task_started)
        self.task_runner.task_failed.connect(self._on_task_failed)
        self.task_runner.busy_changed.connect(self._set_busy)
        self.task_runner.task_rejected.connect(lambda message: QMessageBox.information(self, "MCW Launcher", message))

        controllers = (
            self.version_controller,
            self.account_controller,
            self.instance_controller,
            self.instance_settings_controller,
            self.gui_settings_controller,
            self.launch_controller,
        )
        for controller in controllers:
            controller.status_changed.connect(self._set_status)
            controller.log_created.connect(self.logs_page.append)
            controller.error_created.connect(self._show_error)

    def _initialize_data(self) -> None:
        settings = self.gui_settings_controller.load()
        if settings.get("remember_window_size", True):
            geometry = self.gui_settings_controller.saved_geometry()
            if geometry is not None:
                self.restoreGeometry(geometry)
        self.show_page(settings.get("start_page", "home"))
        self.account_controller.refresh()
        self.instance_controller.refresh()
        self.version_controller.refresh()
        self.logs_page.append(f"Started {LAUNCHER_NAME}")

    def _refresh_all(self) -> None:
        self.account_controller.refresh()
        self.instance_controller.refresh()
        self.version_controller.refresh()
        self._set_status("Refreshing launcher data...")

    def show_page(self, page_id: str) -> None:
        page = self.pages.get(page_id, self.home_page)
        self.content_stack.setCurrentWidget(page)
        self.sidebar.set_current_page(page_id if page_id in self.pages else "home")

    def _account_selected(self, account: object | None) -> None:
        self.home_page.set_account(account)
        self.right_panel.set_account(account)
        self.launch_controller.set_account(account)

    def _instance_selected(self, instance: object | None) -> None:
        self.home_page.set_instance(instance)
        self.right_panel.set_instance(instance)
        self.launch_control.set_selected_instance(instance)
        self.launch_controller.set_instance(instance)
        if instance is not None:
            self.instance_settings_page.select_instance(instance.name)
            self.instance_settings_controller.load(instance.name)

    def _apply_gui_settings(self, settings: dict) -> None:
        self.launcher_settings_page.set_settings(settings)
        self.instances_page.set_show_snapshots(bool(settings.get("show_snapshots", False)))
        self.launch_controller.set_debug_mode(bool(settings.get("debug_mode", False)))

    def _on_task_started(self, _task_id: str, message: str, blocking: bool) -> None:
        if blocking or not self.task_runner.is_busy:
            self._set_status(message)

    def _on_task_failed(self, task_id: str, _error: Exception) -> None:
        if task_id == self.launch_controller.TASK_ID:
            self.launch_control.reset_progress()

    def _on_progress(self, event: object) -> None:
        self.launch_control.set_progress_event(event)
        message = getattr(event, "message", "Working...")
        self.home_page.set_status(message)
        self.right_panel.set_status(message)

    def _set_status(self, message: str) -> None:
        self.home_page.set_status(message)
        self.right_panel.set_status(message)
        self.launch_control.set_status(message)

    def _set_busy(self, busy: bool) -> None:
        self.account_page.set_busy(busy)
        self.instances_page.set_busy(busy)
        self.instance_settings_page.set_busy(busy)
        self.launch_control.set_busy(busy)
        self.right_panel.set_busy(busy)

    def _show_error(self, title: str, message: str) -> None:
        self._set_status(f"{title} failed")
        QMessageBox.critical(self, title, message)

    def _show_export_finished(self, path: Path) -> None:
        QMessageBox.information(self, "Export complete", f"Saved to:\n{path}")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.task_runner.has_active_tasks:
            QMessageBox.information(self, "MCW Launcher", "A launcher task is still running. Close the window after it finishes.")
            event.ignore()
            return
        if self.gui_settings_controller.current.get("remember_window_size", True):
            self.gui_settings_controller.save_geometry(self.saveGeometry())
        self.task_runner.close()
        super().closeEvent(event)


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MCW Launcher")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
