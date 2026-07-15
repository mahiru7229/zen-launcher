from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from src.core.diagnostics.diagnostics_manager import DiagnosticsManager
from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.language.language_manager import language_manager, tr
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.runtime.game_runtime_manager import GameRuntimeManager
from src.core.update.windows_update_installer import AutomaticUpdateUnsupportedError, WindowsUpdateInstaller
from src.gui.config import LAUNCHER_NAME, MINIMUM_HEIGHT, MINIMUM_WIDTH, RIGHT_PANEL_WIDTH, SIDEBAR_WIDTH, VERSION_ID, WINDOW_HEIGHT, WINDOW_WIDTH
from src.gui.controllers.account_controller import AccountController
from src.gui.controllers.backup_controller import BackupController
from src.gui.controllers.java_controller import JavaController
from src.gui.controllers.modpack_lifecycle_controller import ModpackLifecycleController
from src.gui.controllers.gui_settings_controller import GuiSettingsController
from src.gui.controllers.instance_controller import InstanceController
from src.gui.controllers.launch_controller import LaunchController
from src.gui.controllers.mod_controller import ModController
from src.gui.controllers.mod_loader_controller import ModLoaderController
from src.gui.controllers.modrinth_controller import ModrinthController
from src.gui.controllers.settings_controller import InstanceSettingsController
from src.gui.controllers.version_controller import VersionController
from src.gui.controllers.update_controller import UpdateController
from src.gui.dialogs.mod_manager_dialog import ModManagerDialog
from src.gui.dialogs.modrinth_browser_dialog import ModrinthBrowserDialog
from src.gui.dialogs.update_dialog import UpdateDialog
from src.gui.input_guard import install_combo_box_wheel_guard
from src.gui.localization import retranslate_widget_tree
from src.gui.pages.about_page import AboutPage
from src.gui.pages.account_page import AccountPage
from src.gui.pages.home_page import HomePage
from src.gui.pages.instance_settings_page import InstanceSettingsPage
from src.gui.pages.instances_page import InstancesPage
from src.gui.pages.launcher_settings_page import LauncherSettingsPage
from src.gui.pages.logs_page import LogsPage
from src.gui.style import APP_STYLE
from src.gui.task_runner import TaskRunner
from src.gui.theme.runtime import ThemeRuntime
from src.gui.widget.launch_control_style import LAUNCH_CONTROL_STYLE
from src.gui.widget.launch_control_widget import LaunchControlWidget
from src.gui.widget.right_panel_widget import RightPanelWidget
from src.gui.widget.sidebar_widget import SidebarWidget
from src.models.update.update_info import PreparedUpdate, UpdateInfo


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(LAUNCHER_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MINIMUM_WIDTH, MINIMUM_HEIGHT)

        self.task_runner = TaskRunner(self)
        self.version_controller = VersionController(self.task_runner)
        self.account_controller = AccountController(self.task_runner)
        self.backup_controller = BackupController(self.task_runner)
        self.java_controller = JavaController(self.task_runner)
        self.modpack_lifecycle_controller = ModpackLifecycleController(self.task_runner)
        self.instance_controller = InstanceController(self.task_runner)
        self.mod_loader_controller = ModLoaderController(self.task_runner)
        self.mod_controller = ModController(self.task_runner)
        self.modrinth_controller = ModrinthController(self.task_runner)
        self.instance_settings_controller = InstanceSettingsController()
        self.gui_settings_controller = GuiSettingsController()
        self._startup_settings = self.gui_settings_controller.load()
        self.theme_runtime = ThemeRuntime()
        language_manager.reload()
        language_manager.set_language(self._startup_settings.get("language", "en-US"), notify=False)
        self.launch_controller = LaunchController(self.task_runner)
        self.update_controller = UpdateController(self.task_runner, channel=self._startup_settings.get("update_channel", "beta"))
        self.running_instances_timer = QTimer(self)
        self._modrinth_tasks: set[str] = set()
        self._prompted_update_versions: set[str] = set()
        self._selected_instance: object | None = None
        self.running_instances_timer.setInterval(1000)

        self._build_ui()
        retranslate_widget_tree(self)
        self._connect_signals()

        self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, str(self._startup_settings.get("theme", "mcw-default")))
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
        self.mod_manager_dialog = ModManagerDialog(self)
        self.modrinth_mod_dialog = ModrinthBrowserDialog("mod", self)
        self.modrinth_modpack_dialog = ModrinthBrowserDialog("modpack", self)

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
        self.right_panel.manage_mods_requested.connect(self._open_mod_manager)
        self.right_panel.refresh_requested.connect(self._refresh_all)
        self.running_instances_timer.timeout.connect(self.instance_controller.refresh_running)

        self.account_page.create_offline_requested.connect(self.account_controller.create_offline)
        self.account_page.create_microsoft_requested.connect(self.account_controller.create_microsoft)
        self.account_page.cancel_microsoft_requested.connect(self.account_controller.cancel_microsoft)
        self.account_page.select_requested.connect(self.account_controller.select)
        self.account_page.remove_requested.connect(self.account_controller.remove)
        self.account_page.refresh_requested.connect(self.account_controller.refresh)
        self.account_page.security_audit_requested.connect(self.account_controller.audit_security)
        self.account_page.security_reprotect_requested.connect(self.account_controller.reprotect_security)

        self.instances_page.refresh_requested.connect(self.instance_controller.refresh)
        self.instances_page.selected_instance_changed.connect(self.instance_controller.select)
        self.instances_page.create_requested.connect(self.instance_controller.create)
        self.instances_page.fabric_versions_requested.connect(self.mod_loader_controller.load_fabric_versions)
        self.instances_page.loader_change_requested.connect(self.instance_controller.change_loader)
        self.instances_page.repair_loader_requested.connect(self.instance_controller.repair_loader)
        self.instances_page.repair_instance_requested.connect(self.instance_controller.repair_instance)
        self.instances_page.manage_mods_requested.connect(self._open_mod_manager)
        self.instances_page.browse_modpacks_requested.connect(self._open_modrinth_modpacks)
        self.instances_page.rename_requested.connect(self.instance_controller.rename)
        self.instances_page.clone_requested.connect(self.instance_controller.clone)
        self.instances_page.delete_requested.connect(self.instance_controller.delete)
        self.instances_page.import_requested.connect(self.instance_controller.import_package)
        self.instances_page.export_requested.connect(self.instance_controller.export_package)
        self.instances_page.backup_requested.connect(self.backup_controller.create)
        self.instances_page.restore_backup_requested.connect(self.backup_controller.restore)
        self.instances_page.open_backups_requested.connect(self._open_backups_folder)
        self.instances_page.scan_modpack_requested.connect(self.modpack_lifecycle_controller.scan)
        self.instances_page.check_modpack_update_requested.connect(lambda name: self.modpack_lifecycle_controller.check_update(name, self.modrinth_modpack_dialog.allowed_version_types, force_refresh=True))
        self.instances_page.apply_modpack_update_requested.connect(lambda name: self.modpack_lifecycle_controller.update(name, self.modrinth_modpack_dialog.allowed_version_types))

        self.instance_settings_page.load_requested.connect(self.instance_settings_controller.load)
        self.instance_settings_page.save_requested.connect(self.instance_settings_controller.save)

        self.launcher_settings_page.save_requested.connect(self.gui_settings_controller.save)
        self.launcher_settings_page.reset_requested.connect(self.gui_settings_controller.reset)
        self.launcher_settings_page.language_changed.connect(self._preview_language)
        self.launcher_settings_page.check_updates_requested.connect(lambda: self.update_controller.check(manual=True))
        self.launcher_settings_page.reload_theme_requested.connect(self._preview_theme)
        self.launcher_settings_page.scan_java_requested.connect(self.java_controller.scan)
        self.launcher_settings_page.open_java_requested.connect(self._open_java_folder)
        self.logs_page.export_diagnostics_requested.connect(self._export_diagnostics)
        self.logs_page.open_logs_folder_requested.connect(self._open_logs_folder)
        self.logs_page.open_latest_game_log_requested.connect(self._open_latest_game_log)
        self.logs_page.open_latest_crash_report_requested.connect(self._open_latest_crash_report)

        self.launch_control.launch_clicked.connect(self.launch_controller.launch)

        self.version_controller.versions_changed.connect(self.instances_page.set_versions)
        self.version_controller.versions_changed.connect(lambda versions: self.home_page.set_manifest_count(len(versions)))
        self.mod_loader_controller.fabric_versions_changed.connect(self.instances_page.set_fabric_versions)

        self.account_controller.accounts_changed.connect(self.account_page.set_accounts)
        self.account_controller.selected_account_changed.connect(self._account_selected)
        self.account_controller.microsoft_auth_state_changed.connect(self.account_page.set_microsoft_auth_state)
        self.account_controller.security_report_changed.connect(self.account_page.set_security_report)
        self.java_controller.installations_changed.connect(self.launcher_settings_page.set_java_installations)
        self.backup_controller.backup_created.connect(self._on_backup_created)
        self.backup_controller.restore_finished.connect(self._on_backup_restored)
        self.modpack_lifecycle_controller.state_changed.connect(self.instances_page.set_modpack_state)
        self.modpack_lifecycle_controller.update_checked.connect(self._on_modpack_update_checked)
        self.modpack_lifecycle_controller.update_finished.connect(self._on_modpack_updated)

        self.instance_controller.instances_changed.connect(self.instances_page.set_instances)
        self.instance_controller.instances_changed.connect(self.instance_settings_page.set_instances)
        self.instance_controller.running_instances_changed.connect(self.right_panel.set_running_instances)
        self.instance_controller.selected_instance_changed.connect(self._instance_selected)
        self.instance_controller.export_finished.connect(self._show_export_finished)

        self.instance_settings_controller.settings_loaded.connect(self.instance_settings_page.set_settings)
        self.gui_settings_controller.settings_changed.connect(self._apply_gui_settings)

        self.mod_manager_dialog.refresh_requested.connect(self.mod_controller.refresh)
        self.mod_manager_dialog.add_requested.connect(self.mod_controller.add)
        self.mod_manager_dialog.remove_requested.connect(self.mod_controller.remove)
        self.mod_manager_dialog.enabled_requested.connect(self.mod_controller.set_enabled)
        self.mod_manager_dialog.modrinth_requested.connect(self._open_modrinth_mod_browser)
        self.mod_manager_dialog.check_updates_requested.connect(self.mod_controller.check_updates)
        self.mod_manager_dialog.update_projects_requested.connect(self.mod_controller.update_projects)
        self.mod_manager_dialog.update_all_requested.connect(self.mod_controller.update_all)
        self.mod_manager_dialog.lock_requested.connect(self.mod_controller.set_locked)
        self.mod_manager_dialog.analyze_requested.connect(self.mod_controller.analyze)
        self.mod_controller.instance_changed.connect(self.mod_manager_dialog.set_instance)
        self.mod_controller.mods_changed.connect(self.mod_manager_dialog.set_mods)
        self.mod_controller.updates_changed.connect(self.mod_manager_dialog.set_update_report)
        self.mod_controller.health_changed.connect(self.mod_manager_dialog.set_health_report)

        self.modrinth_mod_dialog.search_requested.connect(self._search_modrinth_mods)
        self.modrinth_modpack_dialog.search_requested.connect(self._search_modrinth_modpacks)
        self.modrinth_mod_dialog.versions_requested.connect(self.modrinth_controller.load_versions)
        self.modrinth_modpack_dialog.versions_requested.connect(self.modrinth_controller.load_versions)
        self.modrinth_mod_dialog.install_mod_requested.connect(self._install_modrinth_mod)
        self.modrinth_modpack_dialog.install_modpack_requested.connect(self.modrinth_controller.install_modpack)
        self.modrinth_mod_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.modrinth_modpack_dialog.channel_preferences_changed.connect(self._set_modrinth_channel_preferences)
        self.modrinth_controller.search_results_changed.connect(self._set_modrinth_results)
        self.modrinth_controller.versions_changed.connect(self._set_modrinth_versions)
        self.modrinth_controller.mod_installed.connect(self._modrinth_mod_installed)
        self.modrinth_controller.modpack_installed.connect(self._modrinth_modpack_installed)

        self.launch_controller.progress_received.connect(self._on_progress)
        self.modrinth_controller.progress_received.connect(self._on_progress)
        self.mod_controller.progress_received.connect(self._on_progress)
        self.modpack_lifecycle_controller.progress_received.connect(self._on_progress)
        self.update_controller.progress_received.connect(self._on_progress)
        self.launch_controller.launch_finished.connect(self.launch_control.set_result)
        self.launch_controller.launch_finished.connect(lambda _result: self.instance_controller.refresh_running(force=True))
        self.launch_controller.game_exited.connect(self._on_game_exited)
        self.instance_controller.repair_progress.connect(self._on_progress)
        self.instance_controller.repair_finished.connect(self._on_repair_finished)

        self.update_controller.update_available.connect(self._on_update_available)
        self.update_controller.no_update_available.connect(self._on_no_update_available)
        self.update_controller.update_prepared.connect(self._on_update_prepared)
        self.update_controller.update_check_failed.connect(self._on_update_check_failed)

        self.task_runner.task_started.connect(self._on_task_started)
        self.task_runner.task_failed.connect(self._on_task_failed)
        self.task_runner.task_succeeded.connect(self._on_task_completed)
        self.task_runner.task_failed.connect(self._on_task_completed)
        self.task_runner.busy_changed.connect(self._set_busy)
        self.task_runner.busy_changed.connect(self.mod_manager_dialog.set_busy)
        self.task_runner.task_rejected.connect(lambda message: QMessageBox.information(self, tr("MCW Launcher"), tr(message)))

        controllers = (
            self.version_controller,
            self.account_controller,
            self.backup_controller,
            self.java_controller,
            self.modpack_lifecycle_controller,
            self.instance_controller,
            self.mod_loader_controller,
            self.mod_controller,
            self.modrinth_controller,
            self.instance_settings_controller,
            self.gui_settings_controller,
            self.launch_controller,
            self.update_controller,
        )

        for controller in controllers:
            controller.status_changed.connect(self._set_status)
            controller.log_created.connect(self.logs_page.append)
            controller.error_created.connect(self._show_error)

    def _initialize_data(self) -> None:
        settings = dict(self._startup_settings)
        self._apply_gui_settings(settings)

        if settings.get("remember_window_size", True):
            geometry = self.gui_settings_controller.saved_geometry()

            if geometry is not None:
                self.restoreGeometry(geometry)

        self.show_page(settings.get("start_page", "home"))
        self.account_controller.refresh()
        self.account_controller.audit_security()
        self.instance_controller.refresh()
        self.instance_controller.refresh_running(force=True)
        self.running_instances_timer.start()
        self.version_controller.refresh()
        self.java_controller.scan()
        self.logs_page.append(tr("Started {launcher_name}", launcher_name=LAUNCHER_NAME))
        if settings.get("auto_check_updates", True):
            QTimer.singleShot(1500, lambda: self.update_controller.check(manual=False))

    def _refresh_all(self) -> None:
        self.account_controller.refresh()
        self.instance_controller.refresh()
        self.instance_controller.refresh_running(force=True)
        self.version_controller.refresh()
        self._set_status("Refreshing launcher data...")

    def show_page(self, page_id: str) -> None:
        page = self.pages.get(page_id, self.home_page)

        self.content_stack.setCurrentWidget(page)
        self.sidebar.set_current_page(page_id if page_id in self.pages else "home")

    def _open_mod_manager(self, instance_name: str) -> None:
        instance_name = instance_name.strip()
        if not instance_name:
            QMessageBox.information(self, tr("Mod Manager"), tr("Select an instance first."))
            return
        try:
            instance = InstanceManager.load(instance_name)
        except Exception as error:
            self._show_error(tr("Mod Manager"), str(error))
            return
        self.mod_controller.set_instance(instance)
        self.mod_manager_dialog.show()
        self.mod_manager_dialog.raise_()
        self.mod_manager_dialog.activateWindow()
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name == ModLoaderManager.FABRIC and not self.task_runner.is_task_active("mods.update.check"):
            QTimer.singleShot(0, lambda: self.mod_controller.check_updates(self.mod_manager_dialog.allowed_version_types, force_refresh=False))

    def _open_modrinth_mod_browser(self) -> None:
        instance = self.mod_controller.current_instance
        if instance is None:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.mod.no_instance"))
            return
        self.modrinth_mod_dialog.set_instance(instance)
        self.modrinth_mod_dialog.show()
        self.modrinth_mod_dialog.raise_()
        self.modrinth_mod_dialog.activateWindow()
        self.modrinth_controller.search("mod", "", "downloads", 0, game_version=instance.version_id)

    def _open_modrinth_modpacks(self) -> None:
        self.modrinth_modpack_dialog.set_instance(None)
        self.modrinth_modpack_dialog.show()
        self.modrinth_modpack_dialog.raise_()
        self.modrinth_modpack_dialog.activateWindow()
        self.modrinth_controller.search("modpack", "", "downloads", 0)

    def _search_modrinth_mods(self, project_type: str, query: str, index: str, offset: int) -> None:
        self.modrinth_controller.search(project_type, query, index, offset, game_version=self.modrinth_mod_dialog.game_version)

    def _search_modrinth_modpacks(self, project_type: str, query: str, index: str, offset: int) -> None:
        self.modrinth_controller.search(project_type, query, index, offset)

    def _install_modrinth_mod(self, version_id: str) -> None:
        instance = self.mod_controller.current_instance
        if instance is None:
            QMessageBox.information(self, tr("modrinth.title"), tr("modrinth.mod.no_instance"))
            return
        self.modrinth_controller.install_mod(instance.name, version_id, self.modrinth_mod_dialog.allowed_version_types)

    def _set_modrinth_results(self, project_type: str, result: object) -> None:
        dialog = self.modrinth_mod_dialog if project_type == "mod" else self.modrinth_modpack_dialog
        dialog.set_search_result(result)

    def _set_modrinth_versions(self, project_type: str, project_id: str, versions: list) -> None:
        dialog = self.modrinth_mod_dialog if project_type == "mod" else self.modrinth_modpack_dialog
        dialog.set_versions(project_id, versions)

    def _modrinth_mod_installed(self, result: object) -> None:
        self.mod_controller.refresh()
        if self.mod_manager_dialog.isVisible():
            self.mod_controller.check_updates(self.mod_manager_dialog.allowed_version_types, force_refresh=False)
        count = len(getattr(result, "installed_files", ()) or ())
        warnings = tuple(getattr(result, "warnings", ()) or ())
        message = tr("modrinth.mod.installed", count=count)
        if warnings:
            message += "\n\n" + "\n".join(str(item) for item in warnings)
        QMessageBox.information(self, tr("modrinth.mod.install"), message)

    def _modrinth_modpack_installed(self, result: object) -> None:
        instance = getattr(result, "instance", None)
        selected_name = str(getattr(instance, "name", ""))
        self.instance_controller.refresh(selected_name=selected_name)
        self.modrinth_modpack_dialog.close()
        QMessageBox.information(self, tr("modrinth.modpack.install"), tr("modrinth.modpack.installed", name=selected_name))


    def _open_java_folder(self, installation: object) -> None:
        if installation is None:
            return
        executable = Path(getattr(installation, "executable", ""))
        directory = executable.parent.parent if executable.parent.name.casefold() == "bin" else executable.parent
        if not directory.exists():
            self._show_error(tr("Java installations"), tr("The selected Java directory no longer exists."))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.resolve())))

    def _open_backups_folder(self, instance_name: str) -> None:
        name = str(instance_name).strip()
        if not name:
            return
        try:
            directory = Paths.instance_backups_dir(InstanceManager.load(name))
        except Exception as error:
            self._show_error(tr("Instance backups"), str(error))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory.resolve())))

    def _on_backup_created(self, result: object) -> None:
        backup = getattr(result, "backup", None)
        path = getattr(backup, "path", "")
        self.instance_controller.refresh(selected_name=str(getattr(self._selected_instance, "name", "")))
        QMessageBox.information(self, tr("Instance backup"), tr("Backup created successfully:\n{path}", path=path))

    def _on_backup_restored(self, result: object) -> None:
        name = str(getattr(result, "instance_name", ""))
        safety = getattr(result, "safety_backup", None)
        self.instance_controller.refresh(selected_name=name)
        message = tr("Backup restored successfully for '{name}'.", name=name)
        if safety:
            message += tr("\nSafety backup: {path}", path=safety)
        QMessageBox.information(self, tr("Restore backup"), message)

    def _on_modpack_update_checked(self, info: object) -> None:
        self.instances_page.set_modpack_update_info(info)
        if info is not None and getattr(info, "available", False):
            self.logs_page.append(tr("Modpack update available: {current} → {target}", current=getattr(info, "current_version_number", "?"), target=getattr(info, "target_version_number", "?")))

    def _on_modpack_updated(self, result: object) -> None:
        name = str(getattr(result, "instance_name", ""))
        self.instance_controller.refresh(selected_name=name)
        preserved = tuple(getattr(result, "preserved_files", ()) or ())
        message = tr("Updated '{name}' to modpack version {version}.", name=name, version=getattr(result, "target_version", "?"))
        if preserved:
            message += tr("\n{count} user-modified file(s) were preserved.", count=len(preserved))
        message += tr("\nSafety backup: {path}", path=getattr(result, "backup_path", ""))
        QMessageBox.information(self, tr("Update Modrinth modpack"), message)

    def _on_game_exited(self, result: object) -> None:
        selected_name = str(getattr(self._selected_instance, "name", ""))
        result_name = str(getattr(result, "instance_name", ""))
        if not selected_name or selected_name == result_name:
            self.launch_control.set_exit_result(result)
        self.instance_controller.refresh_running(force=True)
        crashed = bool(getattr(result, "crashed", False))
        instance_name = str(getattr(result, "instance_name", "Minecraft"))
        exit_code = int(getattr(result, "exit_code", -1))
        duration = int(getattr(result, "duration_seconds", 0))
        if crashed:
            message = tr("Minecraft crashed: {name} (exit code {code})", name=instance_name, code=exit_code)
            self.home_page.set_status(message)
            self.right_panel.set_status(message)
            self.logs_page.append(tr("Crash detected after {seconds} second(s).", seconds=duration))
            crash_report = getattr(result, "crash_report_path", None)
            if crash_report:
                self.logs_page.append(tr("Crash report: {path}", path=crash_report))
        else:
            message = tr("Minecraft closed normally: {name}", name=instance_name)
            self.home_page.set_status(message)
            self.right_panel.set_status(message)
            self.logs_page.append(tr("Game session completed in {seconds} second(s).", seconds=duration))

    def _on_repair_finished(self, result: object) -> None:
        instance_name = str(getattr(result, "instance_name", ""))
        libraries = int(getattr(result, "libraries_checked", 0))
        self.launch_control.reset_progress()
        self.logs_page.append(tr("Repair completed for '{name}'. Libraries checked: {count}.", name=instance_name, count=libraries))
        QMessageBox.information(self, tr("Repair instance"), tr("Repair completed for '{name}'. Client, libraries, assets, natives, mod loader, and Java were verified.", name=instance_name))

    def _on_update_available(self, info: UpdateInfo, manual: bool) -> None:
        if not manual and info.version in self._prompted_update_versions:
            return
        self._prompted_update_versions.add(info.version)
        self.launcher_settings_page.set_update_status(tr("update.status.available", version=info.version))

        decision = UpdateDialog.ask(info, self)
        if decision == UpdateDialog.DONT_ASK_AGAIN:
            self.gui_settings_controller.set_auto_check_updates(False)
            self.launcher_settings_page.set_update_status(tr("update.status.auto_disabled"))
            return
        if decision == UpdateDialog.UPDATE_NOW:
            if not WindowsUpdateInstaller.is_supported():
                QMessageBox.information(self, tr("update.error.title"), tr("update.error.packaged_only"))
                return
            blocked_reason = self._update_install_block_reason()
            if blocked_reason:
                QMessageBox.warning(self, tr("update.error.title"), blocked_reason)
                self.launcher_settings_page.set_update_status(tr("update.status.waiting"))
                return
            self.update_controller.prepare(info)

    def _on_no_update_available(self, manual: bool) -> None:
        self.launcher_settings_page.set_update_status(tr("update.status.latest"))
        if manual:
            QMessageBox.information(self, tr("update.latest.title"), tr("update.latest.message"))

    def _on_update_check_failed(self, error: Exception, manual: bool) -> None:
        self.launcher_settings_page.set_update_status(tr("update.status.failed"))
        if manual:
            QMessageBox.warning(self, tr("update.error.title"), tr("update.error.check_failed", error=error))

    def _on_update_prepared(self, prepared: PreparedUpdate) -> None:
        blocked_reason = self._update_install_block_reason()
        if blocked_reason:
            self.launcher_settings_page.set_update_status(tr("update.status.waiting"))
            QMessageBox.warning(self, tr("update.error.title"), blocked_reason)
            return
        self.launcher_settings_page.set_update_status(tr("update.status.installing"))
        QTimer.singleShot(0, lambda: self._launch_prepared_update(prepared))

    def _update_install_block_reason(self) -> str | None:
        active_tasks = [task_id for task_id in self.task_runner.active_task_ids if not task_id.startswith("update.")]
        if active_tasks:
            return tr("update.error.tasks_running", count=len(active_tasks))
        running_instances = InstanceRunLock.list_active()
        if running_instances:
            names = ", ".join(item.name for item in running_instances[:4])
            if len(running_instances) > 4:
                names += f" (+{len(running_instances) - 4})"
            return tr("update.error.instances_running", names=names)
        return None

    def _launch_prepared_update(self, prepared: PreparedUpdate) -> None:
        try:
            WindowsUpdateInstaller.launch(prepared)
        except (AutomaticUpdateUnsupportedError, OSError, RuntimeError) as error:
            self._show_error(tr("update.error.title"), str(error))
            self.launcher_settings_page.set_update_status(tr("update.status.failed"))
            return
        self.close()

    def _account_selected(self, account: object | None) -> None:
        self.home_page.set_account(account)
        self.right_panel.set_account(account)
        self.launch_controller.set_account(account)

    def _instance_selected(self, instance: object | None) -> None:
        self._selected_instance = instance
        self.home_page.set_instance(instance)
        self.right_panel.set_instance(instance)
        self.launch_control.set_selected_instance(instance)
        self.launch_controller.set_instance(instance)

        if instance is not None:
            self.instance_settings_page.select_instance(instance.name)
            self.instance_settings_controller.load(instance.name)
            if (Path(instance.instance_dir) / ".mcw" / "modrinth-pack.json").is_file():
                QTimer.singleShot(0, lambda name=instance.name: self.modpack_lifecycle_controller.scan(name))

    def _apply_gui_settings(self, settings: dict) -> None:
        requested_locale = str(settings.get("language", "en-US"))
        previous_locale = language_manager.current_locale
        language_manager.reload()
        language_manager.set_language(requested_locale, notify=False)
        if language_manager.current_locale != previous_locale:
            self._retranslate_ui()
        self.launcher_settings_page.set_settings(settings)
        self.instances_page.set_show_snapshots(bool(settings.get("show_snapshots", False)))
        self.launch_controller.set_debug_mode(bool(settings.get("debug_mode", False)))
        self.update_controller.set_channel(str(settings.get("update_channel", "beta")))
        include_beta = bool(settings.get("modrinth_include_beta", False))
        include_alpha = bool(settings.get("modrinth_include_alpha", False))
        self.modrinth_mod_dialog.set_channel_preferences(include_beta, include_alpha)
        self.modrinth_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.mod_manager_dialog.set_channel_preferences(include_beta, include_alpha)
        self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, str(settings.get("theme", "mcw-default")), bool(settings.get("show_static_text", True)))

    def _preview_theme(self, theme_id: str) -> None:
        selected = self.theme_runtime.apply(self, APP_STYLE + "\n" + LAUNCH_CONTROL_STYLE, theme_id, self.launcher_settings_page.show_static_text.isChecked())
        self.logs_page.append(f"Theme preview: {selected}")

    def _set_modrinth_channel_preferences(self, include_beta: bool, include_alpha: bool) -> None:
        self.modrinth_mod_dialog.set_channel_preferences(include_beta, include_alpha)
        self.modrinth_modpack_dialog.set_channel_preferences(include_beta, include_alpha)
        self.mod_manager_dialog.set_channel_preferences(include_beta, include_alpha)
        self.gui_settings_controller.set_modrinth_channels(include_beta, include_alpha)

    def _preview_language(self, locale: str) -> None:
        if language_manager.set_language(locale, notify=False):
            self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        retranslate_widget_tree(self)
        self.setWindowTitle(tr(LAUNCHER_NAME))

        for widget in (
            self.home_page,
            self.account_page,
            self.instances_page,
            self.launch_control,
            self.right_panel,
            self.mod_manager_dialog,
            self.modrinth_mod_dialog,
            self.modrinth_modpack_dialog,
        ):
            retranslate_dynamic = getattr(widget, "retranslate_dynamic", None)
            if callable(retranslate_dynamic):
                retranslate_dynamic()
        self.theme_runtime.reapply_assets(self)

    def _on_task_started(self, _task_id: str, message: str, blocking: bool) -> None:
        if _task_id == "mods.update.check":
            self.mod_manager_dialog.set_update_checking(True)
            return
        if _task_id.startswith("modpack."):
            self.instances_page.set_modpack_busy(True)
        if _task_id.startswith("update."):
            self.launcher_settings_page.set_update_busy(True)
            self.launcher_settings_page.set_update_status(message)
        if _task_id.startswith("modrinth."):
            self._modrinth_tasks.add(_task_id)
            self.modrinth_mod_dialog.set_busy(True)
            self.modrinth_modpack_dialog.set_busy(True)
        if blocking or not self.task_runner.is_busy:
            self._set_status(message)

    def _on_task_completed(self, task_id: str, _result: object) -> None:
        if task_id == "mods.update.check":
            self.mod_manager_dialog.set_update_checking(False)
        if task_id.startswith("modpack."):
            self.instances_page.set_modpack_busy(False)
        if task_id.startswith("update."):
            self.launcher_settings_page.set_update_busy(False)
        if not task_id.startswith("modrinth."):
            return
        self._modrinth_tasks.discard(task_id)
        busy = bool(self._modrinth_tasks)
        self.modrinth_mod_dialog.set_busy(busy)
        self.modrinth_modpack_dialog.set_busy(busy)

    def _on_task_failed(self, task_id: str, error: Exception) -> None:
        if task_id == "mods.update.check":
            self.mod_manager_dialog.set_update_error(str(error))
        if task_id == self.launch_controller.TASK_ID:
            self.launch_control.set_failed(str(error))
            self.home_page.set_status("Launch failed")
            self.right_panel.set_status("Launch failed")
            self.instance_controller.refresh_running(force=True)
            return
        if task_id == self.instance_controller.REPAIR_TASK_ID:
            self.launch_control.set_failed(str(error))
            self.home_page.set_status(tr("Repair failed"))
            self.right_panel.set_status(tr("Repair failed"))

    def _on_progress(self, event: object) -> None:
        self.launch_control.set_progress_event(event)

        message = str(getattr(event, "message", "Working..."))
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

    def _export_diagnostics(self) -> None:
        suggested = Paths.diagnostics_default_path()
        selected, _ = QFileDialog.getSaveFileName(self, tr("diagnostics.export.title"), str(suggested), tr("diagnostics.file_filter"))
        if not selected:
            return
        try:
            path = DiagnosticsManager.write_report(Path(selected), launcher_version=VERSION_ID, settings=self.gui_settings_controller.raw_settings(), activity_log=self.logs_page.activity_text())
        except Exception as error:
            self._show_error(tr("diagnostics.export.title"), str(error))
            return
        self.logs_page.append(tr("diagnostics.export.success", path=path))
        QMessageBox.information(self, tr("diagnostics.export.title"), tr("diagnostics.export.success", path=path))

    def _open_logs_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Paths.logs_root().resolve())))


    def _open_latest_game_log(self) -> None:
        instance = self._selected_instance
        if instance is None:
            QMessageBox.information(self, tr("Game log"), tr("Select an instance first."))
            return
        path = GameRuntimeManager.latest_game_log(instance)
        if path is None:
            QMessageBox.information(self, tr("Game log"), tr("No Minecraft log was found for this instance."))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def _open_latest_crash_report(self) -> None:
        instance = self._selected_instance
        if instance is None:
            QMessageBox.information(self, tr("Crash report"), tr("Select an instance first."))
            return
        path = GameRuntimeManager.latest_crash_report(instance)
        if path is None:
            QMessageBox.information(self, tr("Crash report"), tr("No crash report was found for this instance."))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _show_export_finished(self, path: Path) -> None:
        QMessageBox.information(self, tr("Export complete"), tr("Saved to:\n{path}", path=path))

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.task_runner.has_active_tasks:
            QMessageBox.information(
                self,
                tr("MCW Launcher"),
                tr("A launcher task is still running.\nClose the window after it finishes."),
            )
            event.ignore()
            return

        if self.gui_settings_controller.current.get("remember_window_size", True):
            self.gui_settings_controller.save_geometry(self.saveGeometry())

        self.task_runner.close()
        super().closeEvent(event)


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("MCW Launcher")
    app._combo_box_wheel_guard = install_combo_box_wheel_guard(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
