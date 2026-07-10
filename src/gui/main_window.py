import re
import threading
import uuid
import tkinter as tk
from tkinter import messagebox

from src.core.auth.offline_auth import OfflineAuthentication
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


class SimpleLauncher:
    """A minimal offline GUI used to test MCW Launcher's launch pipeline."""

    USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,16}$")

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("MCW Launcher - GUI Test")
        self.root.geometry("520x330")
        self.root.resizable(False, False)

        self.username_var = tk.StringVar()
        self.version_var = tk.StringVar(value="Latest release: checking...")
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self._load_latest_version_async()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, padx=40, pady=30)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="MCW Launcher",
            font=("Segoe UI", 25, "bold"),
        ).pack(pady=(5, 4))

        tk.Label(
            container,
            textvariable=self.version_var,
            font=("Segoe UI", 10),
            fg="#555555",
        ).pack(pady=(0, 24))

        tk.Label(
            container,
            text="Offline username",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x")

        self.username_entry = tk.Entry(
            container,
            textvariable=self.username_var,
            font=("Segoe UI", 13),
            justify="center",
        )
        self.username_entry.pack(fill="x", ipady=7, pady=(6, 15))
        self.username_entry.bind("<Return>", lambda _event: self.launch())
        self.username_entry.focus_set()

        self.launch_button = tk.Button(
            container,
            text="Launch latest Minecraft",
            font=("Segoe UI", 11, "bold"),
            command=self.launch,
            cursor="hand2",
        )
        self.launch_button.pack(fill="x", ipady=7)

        tk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            wraplength=430,
        ).pack(pady=(18, 0))

    def _load_latest_version_async(self) -> None:
        threading.Thread(
            target=self._load_latest_version,
            daemon=True,
        ).start()

    def _load_latest_version(self) -> None:
        version_id = VersionManifestManager.latest_version()

        if version_id:
            self.root.after(
                0,
                self.version_var.set,
                f"Latest release: Minecraft {version_id}",
            )
        else:
            self.root.after(
                0,
                self.version_var.set,
                "Latest release: unavailable",
            )

    def launch(self) -> None:
        username = self.username_var.get().strip()

        if not self.USERNAME_PATTERN.fullmatch(username):
            messagebox.showerror(
                "Invalid username",
                "Username must contain 3-16 letters, numbers, or underscores.",
            )
            return

        self._set_busy(True)
        self.status_var.set("Preparing the latest Minecraft release...")

        threading.Thread(
            target=self._launch_worker,
            args=(username,),
            daemon=True,
        ).start()

    def _launch_worker(self, username: str) -> None:
        try:
            self._set_status("Checking the latest release...")
            version_id = VersionManifestManager.latest_version()

            if not version_id:
                raise RuntimeError(
                    "Could not get the latest Minecraft version. "
                    "Please check your internet connection."
                )

            self._set_version(version_id)
            self._set_status(f"Loading Minecraft {version_id} metadata...")
            version = VersionManager.load(version_id)

            if version is None:
                raise RuntimeError(
                    f"Could not load Minecraft {version_id} metadata."
                )

            instance_name = f"Latest Minecraft {version_id}"

            if InstanceManager.is_instance_exist(instance_name):
                instance = InstanceManager.load(instance_name)
            else:
                self._set_status(f"Creating instance for Minecraft {version_id}...")
                instance = InstanceManager.create(
                    name=instance_name,
                    version=version,
                )

            account = Account(
                account_id=str(uuid.uuid4()),
                account_type=AccountSource.OFFLINE,
                username=username,
                uuid=OfflineAuthentication.uuid_generator(username),
            )
            authentication = OfflineAuthentication.authenticate(account)

            self._set_status(
                "Downloading required files and launching Minecraft..."
            )

            launch_info = MinecraftExecutor.run(
                instance=instance,
                authentication=authentication,
                account=account,
            )

            java_path = launch_info.get("javaPath", "unknown")
            self._set_status(
                f"Minecraft {version_id} started with Java: {java_path}"
            )

        except Exception as error:
            self.root.after(0, self._show_launch_error, str(error))
        finally:
            self.root.after(0, self._set_busy, False)

    def _set_status(self, message: str) -> None:
        self.root.after(0, self.status_var.set, message)

    def _set_version(self, version_id: str) -> None:
        self.root.after(
            0,
            self.version_var.set,
            f"Latest release: Minecraft {version_id}",
        )

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.launch_button.config(state=state)
        self.username_entry.config(state=state)

    def _show_launch_error(self, message: str) -> None:
        self.status_var.set("Launch failed")
        messagebox.showerror("Launch failed", message)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    SimpleLauncher().run()