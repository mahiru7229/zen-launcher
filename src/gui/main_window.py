from __future__ import annotations

import re
import threading
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.core.auth.offline_auth import OfflineAuthentication
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.models.account.account import Account
from src.models.account.account_source import AccountSource
from src.models.progress.progress_event import ProgressEvent


class ExperimentalLauncherGUI:
    """
    Temporary GUI for manually testing MCW Launcher core features.

    This window intentionally keeps presentation simple. Its job is to exercise
    the public core APIs without putting download, filesystem, or launch work on
    Tkinter's main thread.
    """

    USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,16}$")
    INSTANCE_NAME_PATTERN = re.compile(r"^[^<>:\"/\\|?*\x00-\x1F]{1,80}$")
    RELEASE_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("MCW Launcher - Core Test GUI")
        self.root.geometry("780x690")
        self.root.minsize(720, 640)

        self._busy = False
        self._manifest_versions: list[Any] = []

        self.username_var = tk.StringVar(value="Steve")
        self.instance_var = tk.StringVar()
        self.instance_name_var = tk.StringVar()
        self.version_var = tk.StringVar()
        self.show_snapshots_var = tk.BooleanVar(value=False)
        self.include_saves_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="Ready")
        self.progress_text_var = tk.StringVar(value="No task running")
        self.progress_value_var = tk.DoubleVar(value=0.0)

        self._build_ui()
        self._refresh_instances()
        self._run_task(
            self._load_manifest_worker,
            start_message="Loading Minecraft version manifest...",
            lock_ui=False,
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=16)
        root_frame.pack(fill="both", expand=True)

        title = ttk.Label(
            root_frame,
            text="MCW Launcher - Experimental Core Tester",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root_frame,
            text=(
                "Temporary interface for testing instances, packages, "
                "downloads, progress events, Java selection, and launch."
            ),
            wraplength=730,
        )
        subtitle.pack(anchor="w", pady=(2, 14))

        self._build_account_section(root_frame)
        self._build_version_section(root_frame)
        self._build_instance_section(root_frame)
        self._build_progress_section(root_frame)
        self._build_log_section(root_frame)

    def _build_account_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Offline account",
            padding=10,
        )
        frame.pack(fill="x", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Username").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
        )

        self.username_entry = ttk.Entry(
            frame,
            textvariable=self.username_var,
        )
        self.username_entry.grid(
            row=0,
            column=1,
            sticky="ew",
        )
        self.username_entry.bind(
            "<Return>",
            lambda _event: self.launch_selected_instance(),
        )

        ttk.Label(
            frame,
            text="3-16 letters, numbers, or underscores",
        ).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(4, 0),
        )

    def _build_version_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Minecraft version",
            padding=10,
        )
        frame.pack(fill="x", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Version").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 10),
        )

        self.version_combo = ttk.Combobox(
            frame,
            textvariable=self.version_var,
            state="readonly",
        )
        self.version_combo.grid(
            row=0,
            column=1,
            sticky="ew",
        )

        self.snapshot_check = ttk.Checkbutton(
            frame,
            text="Show snapshots",
            variable=self.show_snapshots_var,
            command=self._apply_version_filter,
        )
        self.snapshot_check.grid(
            row=0,
            column=2,
            padx=(10, 0),
        )

        self.refresh_versions_button = ttk.Button(
            frame,
            text="Refresh manifest",
            command=lambda: self._run_task(
                self._load_manifest_worker,
                start_message="Refreshing version manifest...",
                lock_ui=True,
            ),
        )
        self.refresh_versions_button.grid(
            row=0,
            column=3,
            padx=(10, 0),
        )

    def _build_instance_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Instance operations",
            padding=10,
        )
        frame.pack(fill="x", pady=(0, 10))

        for column in range(4):
            frame.columnconfigure(column, weight=1)

        ttk.Label(frame, text="Selected instance").grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.instance_combo = ttk.Combobox(
            frame,
            textvariable=self.instance_var,
            state="readonly",
        )
        self.instance_combo.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(4, 8),
            padx=(0, 8),
        )
        self.instance_combo.bind(
            "<<ComboboxSelected>>",
            self._on_instance_selected,
        )

        self.refresh_instances_button = ttk.Button(
            frame,
            text="Refresh",
            command=self._refresh_instances,
        )
        self.refresh_instances_button.grid(
            row=1,
            column=3,
            sticky="ew",
            pady=(4, 8),
        )

        ttk.Label(
            frame,
            text="New name / rename target / clone target",
        ).grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="w",
        )

        self.instance_name_entry = ttk.Entry(
            frame,
            textvariable=self.instance_name_var,
        )
        self.instance_name_entry.grid(
            row=3,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(4, 8),
        )

        self.create_button = ttk.Button(
            frame,
            text="Create",
            command=self.create_instance,
        )
        self.create_button.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=(0, 4),
            pady=4,
        )

        self.rename_button = ttk.Button(
            frame,
            text="Rename",
            command=self.rename_instance,
        )
        self.rename_button.grid(
            row=4,
            column=1,
            sticky="ew",
            padx=4,
            pady=4,
        )

        self.clone_button = ttk.Button(
            frame,
            text="Clone",
            command=self.clone_instance,
        )
        self.clone_button.grid(
            row=4,
            column=2,
            sticky="ew",
            padx=4,
            pady=4,
        )

        self.delete_button = ttk.Button(
            frame,
            text="Delete",
            command=self.delete_instance,
        )
        self.delete_button.grid(
            row=4,
            column=3,
            sticky="ew",
            padx=(4, 0),
            pady=4,
        )

        self.import_button = ttk.Button(
            frame,
            text="Import .mcwpack",
            command=self.import_instance,
        )
        self.import_button.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=(0, 4),
            pady=4,
        )

        self.export_button = ttk.Button(
            frame,
            text="Export .mcwpack",
            command=self.export_instance,
        )
        self.export_button.grid(
            row=5,
            column=1,
            sticky="ew",
            padx=4,
            pady=4,
        )

        self.include_saves_check = ttk.Checkbutton(
            frame,
            text="Include saves",
            variable=self.include_saves_var,
        )
        self.include_saves_check.grid(
            row=5,
            column=2,
            sticky="w",
            padx=8,
            pady=4,
        )

        self.launch_button = ttk.Button(
            frame,
            text="Launch selected instance",
            command=self.launch_selected_instance,
        )
        self.launch_button.grid(
            row=5,
            column=3,
            sticky="ew",
            padx=(4, 0),
            pady=4,
        )

    def _build_progress_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="Progress",
            padding=10,
        )
        frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame,
            textvariable=self.progress_text_var,
            wraplength=720,
        ).pack(anchor="w", pady=(3, 8))

        self.progress_bar = ttk.Progressbar(
            frame,
            variable=self.progress_value_var,
            maximum=100.0,
            mode="determinate",
        )
        self.progress_bar.pack(fill="x")

    def _build_log_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(
            parent,
            text="GUI event log",
            padding=8,
        )
        frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            frame,
            height=10,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.log_text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.log_text.yview,
        )
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(
            yscrollcommand=scrollbar.set,
        )

    # ------------------------------------------------------------------
    # Generic threading helpers
    # ------------------------------------------------------------------

    def _run_task(
        self,
        worker: Callable[[], Any],
        *,
        start_message: str,
        lock_ui: bool = True,
        on_success: Callable[[Any], None] | None = None,
    ) -> None:
        if lock_ui and self._busy:
            messagebox.showinfo(
                "Task already running",
                "Wait for the current task to finish.",
            )
            return

        if lock_ui:
            self._set_busy(True)

        self._set_status(start_message)
        self._append_log(start_message)

        def runner() -> None:
            try:
                result = worker()
            except Exception as error:
                self.root.after(
                    0,
                    self._handle_task_error,
                    error,
                )
            else:
                if on_success is not None:
                    self.root.after(
                        0,
                        on_success,
                        result,
                    )
            finally:
                if lock_ui:
                    self.root.after(
                        0,
                        self._set_busy,
                        False,
                    )

        threading.Thread(
            target=runner,
            daemon=True,
        ).start()

    def _handle_task_error(
        self,
        error: Exception,
    ) -> None:
        message = f"{type(error).__name__}: {error}"
        self._set_status("Task failed")
        self._append_log(message)
        self._stop_indeterminate_progress()
        messagebox.showerror(
            "MCW Launcher test GUI",
            message,
        )

    # ------------------------------------------------------------------
    # Version operations
    # ------------------------------------------------------------------

    def _load_manifest_worker(self) -> list[Any]:
        versions = VersionManifestManager.get()

        if not versions:
            raise RuntimeError(
                "The Minecraft version manifest is unavailable."
            )

        self._manifest_versions = versions

        self.root.after(
            0,
            self._apply_version_filter,
        )
        self.root.after(
            0,
            self._set_status,
            f"Loaded {len(versions)} manifest entries",
        )
        self.root.after(
            0,
            self._append_log,
            f"Manifest loaded: {len(versions)} entries",
        )

        return versions

    def _apply_version_filter(self) -> None:
        include_snapshots = (
            self.show_snapshots_var.get()
        )

        version_ids: list[str] = []

        for version in self._manifest_versions:
            version_type = getattr(
                version,
                "type",
                "",
            )

            if version_type == "release":
                if self._is_supported_release(
                    version.id
                ):
                    version_ids.append(version.id)
            elif include_snapshots:
                version_ids.append(version.id)

        self.version_combo["values"] = version_ids

        if (
            self.version_var.get()
            not in version_ids
        ):
            self.version_var.set(
                version_ids[0]
                if version_ids
                else ""
            )

    @classmethod
    def _is_supported_release(
        cls,
        version_id: str,
    ) -> bool:
        match = cls.RELEASE_VERSION_PATTERN.fullmatch(
            version_id
        )

        if match is None:
            return False

        major = int(match.group(1))
        minor = int(match.group(2))

        return (major, minor) >= (1, 13)

    # ------------------------------------------------------------------
    # Instance operations
    # ------------------------------------------------------------------

    def _refresh_instances(
        self,
        selected_name: str | None = None,
    ) -> None:
        try:
            instances = InstanceManager.list_instances()
            names = sorted(
                instance.name
                for instance in instances
            )
        except Exception as error:
            self._handle_task_error(error)
            return

        self.instance_combo["values"] = names

        preferred = (
            selected_name
            or self.instance_var.get()
        )

        if preferred in names:
            self.instance_var.set(preferred)
        elif names:
            self.instance_var.set(names[0])
        else:
            self.instance_var.set("")

        self._append_log(
            f"Instances refreshed: {len(names)} found"
        )

    def _on_instance_selected(
        self,
        _event: tk.Event | None = None,
    ) -> None:
        selected = self.instance_var.get().strip()

        if not selected:
            return

        try:
            instance = InstanceManager.load(selected)
        except Exception as error:
            self._handle_task_error(error)
            return

        self.instance_name_var.set(instance.name)

        version_id = getattr(
            instance,
            "version_id",
            "",
        )

        if version_id:
            self.version_var.set(version_id)

        self._append_log(
            f"Selected instance: {instance.name} "
            f"(Minecraft {version_id})"
        )

    def create_instance(self) -> None:
        name = self._validated_new_instance_name()
        version_id = self._selected_version_id()

        if name is None or version_id is None:
            return

        def worker() -> Any:
            version = VersionManager.load(version_id)

            if version is None:
                raise RuntimeError(
                    f"Unable to load Minecraft {version_id}."
                )

            return InstanceManager.create(
                name=name,
                version=version,
            )

        def success(instance: Any) -> None:
            self._refresh_instances(instance.name)
            self._set_status(
                f"Created instance '{instance.name}'"
            )
            self._append_log(
                f"Created instance '{instance.name}' "
                f"for Minecraft {instance.version_id}"
            )

        self._run_task(
            worker,
            start_message=(
                f"Creating instance '{name}' "
                f"for Minecraft {version_id}..."
            ),
            on_success=success,
        )

    def rename_instance(self) -> None:
        source = self._selected_instance_name()
        target = self._validated_new_instance_name()

        if source is None or target is None:
            return

        if source == target:
            messagebox.showinfo(
                "Rename instance",
                "The new name is the same as the current name.",
            )
            return

        def worker() -> Path:
            return InstanceManager.rename(
                source,
                target,
            )

        def success(path: Path) -> None:
            self._refresh_instances(target)
            self._set_status(
                f"Renamed '{source}' to '{target}'"
            )
            self._append_log(
                f"Renamed instance: {path}"
            )

        self._run_task(
            worker,
            start_message=(
                f"Renaming '{source}' to '{target}'..."
            ),
            on_success=success,
        )

    def clone_instance(self) -> None:
        source = self._selected_instance_name()
        target = self._validated_new_instance_name()

        if source is None or target is None:
            return

        include_saves = (
            self.include_saves_var.get()
        )

        def worker() -> Any:
            return InstanceManager.clone(
                source_name=source,
                new_name=target,
                include_saves=include_saves,
            )

        def success(instance: Any) -> None:
            self._refresh_instances(instance.name)
            self._set_status(
                f"Cloned '{source}' to '{target}'"
            )
            self._append_log(
                f"Clone complete; include_saves={include_saves}"
            )

        self._run_task(
            worker,
            start_message=(
                f"Cloning '{source}' to '{target}'..."
            ),
            on_success=success,
        )

    def delete_instance(self) -> None:
        name = self._selected_instance_name()

        if name is None:
            return

        confirmed = messagebox.askyesno(
            "Delete instance",
            (
                f"Delete '{name}' and its entire instance "
                "directory?\n\nThis cannot be undone."
            ),
        )

        if not confirmed:
            return

        def worker() -> bool:
            return InstanceManager.delete_instance(
                name
            )

        def success(deleted: bool) -> None:
            self._refresh_instances()

            if deleted:
                self._set_status(
                    f"Deleted instance '{name}'"
                )
                self._append_log(
                    f"Deleted instance '{name}'"
                )
            else:
                self._set_status(
                    f"Instance '{name}' was not found"
                )

        self._run_task(
            worker,
            start_message=(
                f"Deleting instance '{name}'..."
            ),
            on_success=success,
        )

    def export_instance(self) -> None:
        name = self._selected_instance_name()

        if name is None:
            return

        output_path = filedialog.asksaveasfilename(
            title="Export MCW instance",
            defaultextension=".mcwpack",
            filetypes=[
                ("MCW package", "*.mcwpack"),
                ("All files", "*.*"),
            ],
            initialfile=f"{name}.mcwpack",
        )

        if not output_path:
            return

        include_saves = (
            self.include_saves_var.get()
        )

        def worker() -> Path:
            return InstanceManager.export(
                instance_name=name,
                output_path=Path(output_path),
                include_saves=include_saves,
            )

        def success(path: Path) -> None:
            self._set_status(
                f"Exported '{name}'"
            )
            self._append_log(
                f"Package exported: {path}"
            )
            messagebox.showinfo(
                "Export complete",
                f"Package saved to:\n{path}",
            )

        self._run_task(
            worker,
            start_message=(
                f"Exporting '{name}'..."
            ),
            on_success=success,
        )

    def import_instance(self) -> None:
        package_path = filedialog.askopenfilename(
            title="Import MCW instance",
            filetypes=[
                ("MCW package", "*.mcwpack"),
                ("ZIP package", "*.zip"),
                ("All files", "*.*"),
            ],
        )

        if not package_path:
            return

        def worker() -> Any:
            return InstanceManager.import_instance(
                Path(package_path)
            )

        def success(instance: Any) -> None:
            self._refresh_instances(instance.name)
            self._set_status(
                f"Imported instance '{instance.name}'"
            )
            self._append_log(
                f"Package imported: {package_path}"
            )

        self._run_task(
            worker,
            start_message=(
                f"Importing package '{Path(package_path).name}'..."
            ),
            on_success=success,
        )

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def launch_selected_instance(self) -> None:
        instance_name = (
            self._selected_instance_name()
        )
        username = (
            self.username_var.get().strip()
        )

        if instance_name is None:
            return

        if not self.USERNAME_PATTERN.fullmatch(
            username
        ):
            messagebox.showerror(
                "Invalid username",
                (
                    "Username must contain 3-16 letters, "
                    "numbers, or underscores."
                ),
            )
            return

        def worker() -> dict:
            instance = InstanceManager.load(
                instance_name
            )

            account = Account(
                account_id=str(uuid.uuid4()),
                account_type=AccountSource.OFFLINE,
                username=username,
                uuid=(
                    OfflineAuthentication.uuid_generator(
                        username
                    )
                ),
            )
            authentication = (
                OfflineAuthentication.authenticate(
                    account
                )
            )

            return MinecraftExecutor.run(
                instance=instance,
                authentication=authentication,
                account=account,
                on_progress=self._on_progress,
            )

        def success(info: dict) -> None:
            java_path = info.get(
                "javaPath",
                "unknown",
            )
            version_id = info.get(
                "minecraftVersion",
                "unknown",
            )

            self._stop_indeterminate_progress()
            self.progress_value_var.set(100.0)
            self._set_status(
                f"Minecraft {version_id} launched"
            )
            self.progress_text_var.set(
                f"Java: {java_path}"
            )
            self._append_log(
                f"Launch complete: Minecraft {version_id}; "
                f"Java={java_path}"
            )

        self._run_task(
            worker,
            start_message=(
                f"Launching instance '{instance_name}'..."
            ),
            on_success=success,
        )

    def _on_progress(
        self,
        event: ProgressEvent,
    ) -> None:
        self.root.after(
            0,
            self._apply_progress_event,
            event,
        )

    def _apply_progress_event(
        self,
        event: ProgressEvent,
    ) -> None:
        self.status_var.set(event.message)

        stage_name = event.stage.value.replace(
            "_",
            " ",
        ).title()

        if event.is_determinate:
            self._stop_indeterminate_progress()

            percentage = event.percentage or 0.0
            self.progress_value_var.set(percentage)

            self.progress_text_var.set(
                (
                    f"{stage_name}: {event.current}/"
                    f"{event.total} "
                    f"({percentage:.1f}%)"
                )
            )
        else:
            self._start_indeterminate_progress()
            self.progress_text_var.set(stage_name)

        self._append_log(
            self._format_progress_event(event)
        )

    @staticmethod
    def _format_progress_event(
        event: ProgressEvent,
    ) -> str:
        if event.is_determinate:
            percentage = event.percentage or 0.0
            return (
                f"[{event.stage.value}] {event.message} "
                f"{event.current}/{event.total} "
                f"({percentage:.1f}%)"
            )

        return (
            f"[{event.stage.value}] {event.message}"
        )

    # ------------------------------------------------------------------
    # Validation and presentation helpers
    # ------------------------------------------------------------------

    def _selected_instance_name(
        self,
    ) -> str | None:
        name = self.instance_var.get().strip()

        if not name:
            messagebox.showerror(
                "No instance selected",
                "Select an instance first.",
            )
            return None

        return name

    def _selected_version_id(
        self,
    ) -> str | None:
        version_id = self.version_var.get().strip()

        if not version_id:
            messagebox.showerror(
                "No version selected",
                "Select a Minecraft version first.",
            )
            return None

        return version_id

    def _validated_new_instance_name(
        self,
    ) -> str | None:
        name = self.instance_name_var.get().strip()

        if not name:
            messagebox.showerror(
                "Invalid instance name",
                "Enter an instance name.",
            )
            return None

        if name in {".", ".."}:
            messagebox.showerror(
                "Invalid instance name",
                "That instance name is not allowed.",
            )
            return None

        if (
            not self.INSTANCE_NAME_PATTERN.fullmatch(
                name
            )
        ):
            messagebox.showerror(
                "Invalid instance name",
                (
                    "The name contains a character "
                    "that Windows cannot use in a folder name."
                ),
            )
            return None

        if name.endswith((" ", ".")):
            messagebox.showerror(
                "Invalid instance name",
                (
                    "The instance name cannot end "
                    "with a space or period."
                ),
            )
            return None

        return name

    def _set_status(
        self,
        message: str,
    ) -> None:
        self.status_var.set(message)

    def _append_log(
        self,
        message: str,
    ) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(
            "end",
            message + "\n",
        )
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _start_indeterminate_progress(self) -> None:
        if str(
            self.progress_bar.cget("mode")
        ) != "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.configure(
                mode="indeterminate"
            )

        self.progress_bar.start(12)

    def _stop_indeterminate_progress(self) -> None:
        self.progress_bar.stop()
        self.progress_bar.configure(
            mode="determinate"
        )

    def _set_busy(
        self,
        busy: bool,
    ) -> None:
        self._busy = busy

        normal_state = (
            tk.DISABLED
            if busy
            else tk.NORMAL
        )
        readonly_state = (
            tk.DISABLED
            if busy
            else "readonly"
        )

        for widget in [
            self.username_entry,
            self.instance_name_entry,
            self.create_button,
            self.rename_button,
            self.clone_button,
            self.delete_button,
            self.import_button,
            self.export_button,
            self.launch_button,
            self.refresh_instances_button,
            self.refresh_versions_button,
            self.snapshot_check,
            self.include_saves_check,
        ]:
            widget.configure(
                state=normal_state
            )

        self.instance_combo.configure(
            state=readonly_state
        )
        self.version_combo.configure(
            state=readonly_state
        )

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ExperimentalLauncherGUI().run()