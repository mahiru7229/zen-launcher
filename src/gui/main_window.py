import re
import threading
import uuid
import tkinter as tk

from tkinter import messagebox, ttk

from src.core.auth.offline_auth import OfflineAuthentication
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import (
    VersionManifestManager,
)
from src.models.account.account import Account
from src.models.account.account_source import AccountSource
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_unit import ProgressUnit


class SimpleLauncher:
    """
    Temporary GUI used to test:

    - Minecraft version selection
    - Offline authentication
    - Instance creation/loading
    - ProgressReporter integration
    - Minecraft launch pipeline
    """

    USERNAME_PATTERN = re.compile(
        r"^[A-Za-z0-9_]{3,16}$"
    )

    MINIMUM_VERSION = (1, 13)

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("MCW Launcher - GUI API Test")
        self.root.geometry("720x620")
        self.root.minsize(650, 560)

        self.username_var = tk.StringVar()
        self.version_var = tk.StringVar()

        self.status_var = tk.StringVar(
            value="Loading Minecraft versions..."
        )

        self.progress_text_var = tk.StringVar(
            value="Waiting..."
        )

        self._versions_by_id: dict[str, object] = {}

        self._build_ui()
        self._load_versions_async()

    def _build_ui(self) -> None:
        container = ttk.Frame(
            self.root,
            padding=24,
        )
        container.pack(
            fill="both",
            expand=True,
        )

        title_label = ttk.Label(
            container,
            text="MCW Launcher",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.pack(
            pady=(0, 5),
        )

        subtitle_label = ttk.Label(
            container,
            text="Minecraft launch and progress API test",
            font=("Segoe UI", 10),
        )
        subtitle_label.pack(
            pady=(0, 22),
        )

        form_frame = ttk.Frame(container)
        form_frame.pack(
            fill="x",
        )

        username_label = ttk.Label(
            form_frame,
            text="Offline username",
            font=("Segoe UI", 10, "bold"),
        )
        username_label.pack(
            anchor="w",
        )

        self.username_entry = ttk.Entry(
            form_frame,
            textvariable=self.username_var,
            font=("Segoe UI", 12),
        )
        self.username_entry.pack(
            fill="x",
            ipady=5,
            pady=(5, 15),
        )

        version_label = ttk.Label(
            form_frame,
            text="Minecraft version (1.13 or newer)",
            font=("Segoe UI", 10, "bold"),
        )
        version_label.pack(
            anchor="w",
        )

        self.version_combobox = ttk.Combobox(
            form_frame,
            textvariable=self.version_var,
            state="disabled",
            font=("Segoe UI", 11),
        )
        self.version_combobox.pack(
            fill="x",
            ipady=4,
            pady=(5, 18),
        )

        self.launch_button = ttk.Button(
            form_frame,
            text="Launch Minecraft",
            command=self.launch,
            state="disabled",
        )
        self.launch_button.pack(
            fill="x",
            ipady=7,
        )

        progress_frame = ttk.LabelFrame(
            container,
            text="Progress",
            padding=14,
        )
        progress_frame.pack(
            fill="x",
            pady=(22, 12),
        )

        self.status_label = ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"),
            wraplength=620,
        )
        self.status_label.pack(
            fill="x",
            anchor="w",
        )

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )
        self.progress_bar.pack(
            fill="x",
            pady=(12, 7),
        )

        self.progress_text_label = ttk.Label(
            progress_frame,
            textvariable=self.progress_text_var,
            font=("Segoe UI", 9),
        )
        self.progress_text_label.pack(
            fill="x",
            anchor="w",
        )

        log_frame = ttk.LabelFrame(
            container,
            text="Progress log",
            padding=8,
        )
        log_frame.pack(
            fill="both",
            expand=True,
        )

        self.log_text = tk.Text(
            log_frame,
            height=12,
            state="disabled",
            wrap="word",
            font=("Consolas", 9),
        )

        scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log_text.yview,
        )

        self.log_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.log_text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.username_entry.bind(
            "<Return>",
            lambda _event: self.launch(),
        )

        self.username_entry.focus_set()

    # =========================================================
    # Version loading
    # =========================================================

    def _load_versions_async(self) -> None:
        threading.Thread(
            target=self._load_versions_worker,
            daemon=True,
        ).start()

    def _load_versions_worker(self) -> None:
        try:
            manifests = VersionManifestManager.get()

            releases = [
                manifest
                for manifest in manifests
                if (
                    manifest.type == "release"
                    and self._is_supported_version(
                        manifest.id
                    )
                )
            ]

            if not releases:
                raise RuntimeError(
                    "No supported Minecraft versions were found."
                )

            # Manifest của Mojang thường đã sắp xếp mới nhất trước.
            version_ids = [
                manifest.id
                for manifest in releases
            ]

            self._versions_by_id = {
                manifest.id: manifest
                for manifest in releases
            }

            self.root.after(
                0,
                self._finish_loading_versions,
                version_ids,
            )

        except Exception as error:
            self.root.after(
                0,
                self._show_version_error,
                str(error),
            )

    def _finish_loading_versions(
        self,
        version_ids: list[str],
    ) -> None:
        self.version_combobox.configure(
            values=version_ids,
            state="readonly",
        )

        self.version_var.set(version_ids[0])

        self.launch_button.configure(
            state="normal"
        )

        self.status_var.set(
            f"Loaded {len(version_ids)} supported releases."
        )

        self.progress_text_var.set(
            "Choose a version and launch."
        )

        self._append_log(
            f"Loaded {len(version_ids)} releases "
            f"from Minecraft 1.13 onward."
        )

    @classmethod
    def _is_supported_version(
        cls,
        version_id: str,
    ) -> bool:
        """
        Accept numeric release IDs such as:

        1.13
        1.13.2
        1.21.8
        26.2

        Reject snapshots and unusual IDs.
        """

        if not re.fullmatch(
            r"\d+(?:\.\d+)*",
            version_id,
        ):
            return False

        try:
            parts = tuple(
                int(part)
                for part in version_id.split(".")
            )
        except ValueError:
            return False

        normalized = parts + (0,) * (
            len(cls.MINIMUM_VERSION) - len(parts)
        )

        return normalized >= cls.MINIMUM_VERSION

    # =========================================================
    # Launching
    # =========================================================

    def launch(self) -> None:
        if str(
            self.launch_button.cget("state")
        ) == "disabled":
            return

        username = self.username_var.get().strip()
        version_id = self.version_var.get().strip()

        if not self.USERNAME_PATTERN.fullmatch(username):
            messagebox.showerror(
                "Invalid username",
                (
                    "Username must contain 3-16 letters, "
                    "numbers, or underscores."
                ),
            )
            return

        if not version_id:
            messagebox.showerror(
                "No version selected",
                "Please select a Minecraft version.",
            )
            return

        self._set_busy(True)
        self._reset_progress()

        self.status_var.set(
            f"Preparing Minecraft {version_id}..."
        )

        self._append_log(
            f"Starting Minecraft {version_id} "
            f"as {username}."
        )

        threading.Thread(
            target=self._launch_worker,
            args=(username, version_id),
            daemon=True,
        ).start()

    def _launch_worker(
        self,
        username: str,
        version_id: str,
    ) -> None:
        try:
            self._set_status(
                f"Loading Minecraft {version_id} metadata..."
            )

            version = VersionManager.load(version_id)

            if version is None:
                raise RuntimeError(
                    f"Could not load Minecraft "
                    f"{version_id} metadata."
                )

            instance_name = (
                f"Minecraft {version_id}"
            )

            if InstanceManager.is_instance_exist(
                instance_name
            ):
                instance = InstanceManager.load(
                    instance_name
                )

                self._append_log_safe(
                    f"Loaded instance: {instance_name}"
                )

            else:
                self._set_status(
                    f"Creating instance for "
                    f"Minecraft {version_id}..."
                )

                instance = InstanceManager.create(
                    name=instance_name,
                    version=version,
                )

                self._append_log_safe(
                    f"Created instance: {instance_name}"
                )

            account = Account(
                account_id=str(uuid.uuid4()),
                account_type=AccountSource.OFFLINE,
                username=username,
                uuid=OfflineAuthentication.uuid_generator(
                    username
                ),
            )

            authentication = (
                OfflineAuthentication.authenticate(
                    account
                )
            )

            launch_info = MinecraftExecutor.run(
                instance=instance,
                authentication=authentication,
                account=account,
                debug_mode=False,
                on_progress=self._handle_progress,
            )

            java_path = launch_info.get(
                "javaPath",
                "unknown",
            )

            self.root.after(
                0,
                self._launch_finished,
                version_id,
                str(java_path),
            )

        except Exception as error:
            self.root.after(
                0,
                self._show_launch_error,
                str(error),
            )

        finally:
            self.root.after(
                0,
                self._set_busy,
                False,
            )

    # =========================================================
    # Progress handling
    # =========================================================

    def _handle_progress(
        self,
        event: ProgressEvent,
    ) -> None:
        """
        Called from the launch worker thread.

        Tkinter widgets must only be changed on the main thread,
        so the event is forwarded through root.after().
        """

        self.root.after(
            0,
            self._render_progress,
            event,
        )

    def _render_progress(
        self,
        event: ProgressEvent,
    ) -> None:
        self.status_var.set(event.message)

        if not event.is_determinate:
            self._set_indeterminate_progress()

            self.progress_text_var.set(
                event.stage.value
            )

            self._append_log(
                f"[{event.stage.value}] "
                f"{event.message}"
            )
            return

        self._set_determinate_progress(
            event.percentage or 0.0
        )

        if event.unit == ProgressUnit.BYTES:
            current_mb = (
                (event.current or 0)
                / 1024
                / 1024
            )

            total_mb = (
                (event.total or 0)
                / 1024
                / 1024
            )

            progress_text = (
                f"{current_mb:.2f} / "
                f"{total_mb:.2f} MB "
                f"({event.percentage:.2f}%)"
            )

        elif event.unit == ProgressUnit.FILES:
            progress_text = (
                f"{event.current} / "
                f"{event.total} files "
                f"({event.percentage:.2f}%)"
            )

        else:
            progress_text = (
                f"{event.percentage:.2f}%"
            )

        self.progress_text_var.set(
            progress_text
        )

        self._append_log(
            f"[{event.stage.value}] "
            f"{event.message} "
            f"{progress_text}"
        )

    def _set_indeterminate_progress(self) -> None:
        if str(
            self.progress_bar.cget("mode")
        ) != "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.configure(
                mode="indeterminate"
            )
            self.progress_bar.start(12)

    def _set_determinate_progress(
        self,
        percentage: float,
    ) -> None:
        if str(
            self.progress_bar.cget("mode")
        ) != "determinate":
            self.progress_bar.stop()
            self.progress_bar.configure(
                mode="determinate"
            )

        self.progress_bar["value"] = percentage

    def _reset_progress(self) -> None:
        self.progress_bar.stop()
        self.progress_bar.configure(
            mode="determinate",
            value=0,
        )

        self.progress_text_var.set(
            "Starting..."
        )

        self.log_text.configure(
            state="normal"
        )
        self.log_text.delete(
            "1.0",
            tk.END,
        )
        self.log_text.configure(
            state="disabled"
        )

    # =========================================================
    # UI helpers
    # =========================================================

    def _set_status(
        self,
        message: str,
    ) -> None:
        self.root.after(
            0,
            self.status_var.set,
            message,
        )

    def _set_busy(
        self,
        busy: bool,
    ) -> None:
        if busy:
            self.launch_button.configure(
                state="disabled"
            )
            self.username_entry.configure(
                state="disabled"
            )
            self.version_combobox.configure(
                state="disabled"
            )
        else:
            self.launch_button.configure(
                state="normal"
            )
            self.username_entry.configure(
                state="normal"
            )
            self.version_combobox.configure(
                state="readonly"
            )

    def _launch_finished(
        self,
        version_id: str,
        java_path: str,
    ) -> None:
        self.progress_bar.stop()
        self.progress_bar.configure(
            mode="determinate",
            value=100,
        )

        self.status_var.set(
            f"Minecraft {version_id} launched successfully."
        )

        self.progress_text_var.set(
            "Launch completed."
        )

        self._append_log(
            f"Minecraft started using Java: {java_path}"
        )

    def _show_launch_error(
        self,
        message: str,
    ) -> None:
        self.progress_bar.stop()

        self.status_var.set(
            "Launch failed."
        )

        self.progress_text_var.set(
            message
        )

        self._append_log(
            f"[error] {message}"
        )

        messagebox.showerror(
            "Launch failed",
            message,
        )

    def _show_version_error(
        self,
        message: str,
    ) -> None:
        self.status_var.set(
            "Could not load Minecraft versions."
        )

        self.progress_text_var.set(
            message
        )

        messagebox.showerror(
            "Version loading failed",
            message,
        )

    def _append_log_safe(
        self,
        message: str,
    ) -> None:
        self.root.after(
            0,
            self._append_log,
            message,
        )

    def _append_log(
        self,
        message: str,
    ) -> None:
        self.log_text.configure(
            state="normal"
        )

        self.log_text.insert(
            tk.END,
            message + "\n",
        )

        self.log_text.see(
            tk.END
        )

        self.log_text.configure(
            state="disabled"
        )

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    SimpleLauncher().run()

