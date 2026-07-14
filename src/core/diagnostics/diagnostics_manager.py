from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager
from src.core.instance.instance_run_lock import InstanceRunLock


class DiagnosticsManager:
    REPORT_SCHEMA_VERSION = 1

    @classmethod
    def build_report(cls, launcher_version: str, settings: dict[str, Any] | None = None, activity_log: str = "") -> str:
        active_instances = InstanceRunLock.list_active()
        try:
            instances = InstanceManager.list_instances()
        except Exception as error:
            instances = []
            instance_error = str(error)
        else:
            instance_error = ""

        safe_settings = cls._safe_settings(settings or {})
        language_files = cls._language_files()
        lines = [
            "MCW Launcher Diagnostic Report",
            "=" * 30,
            f"schema_version: {cls.REPORT_SCHEMA_VERSION}",
            f"generated_at: {datetime.now(timezone.utc).isoformat()}",
            f"launcher_version: {launcher_version}",
            f"packaged: {bool(getattr(sys, 'frozen', False))}",
            f"python: {platform.python_version()}",
            f"platform: {platform.platform()}",
            f"architecture: {platform.machine() or 'unknown'}",
            f"executable: {Path(sys.executable).resolve()}",
            f"working_directory: {Path.cwd().resolve()}",
            f"application_root: {Paths.root().resolve()}",
            "",
            "Data directories",
            "----------------",
            f"config: {Paths.CONFIG_ROOT.resolve()}",
            f"instances: {Paths.INSTANCES_ROOT.resolve()}",
            f"cache: {Paths.CACHE_ROOT.resolve()}",
            f"accounts: {Paths.ACCOUNTS_ROOT.resolve()}",
            f"logs: {Paths.LOGS_ROOT.resolve()}",
            "",
            "Runtime state",
            "-------------",
            f"instance_count: {len(instances)}",
            f"running_instance_count: {len(active_instances)}",
        ]
        if instance_error:
            lines.append(f"instance_scan_error: {instance_error}")
        for item in active_instances:
            lines.append(f"running_instance: {item.name} [{item.state}] pid={item.minecraft_pid or item.launcher_pid or 'unknown'}")

        lines.extend([
            "",
            "Language packs",
            "--------------",
            *(language_files or ["none detected"]),
            "",
            "Launcher settings (safe subset)",
            "-------------------------------",
            json.dumps(safe_settings, ensure_ascii=False, indent=2, sort_keys=True),
        ])

        if activity_log.strip():
            lines.extend(["", "Recent frontend activity", "------------------------", activity_log.strip()])

        return "\n".join(lines).rstrip() + "\n"

    @classmethod
    def write_report(cls, path: Path, launcher_version: str, settings: dict[str, Any] | None = None, activity_log: str = "") -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f"{destination.name}.tmp")
        payload = cls.build_report(launcher_version=launcher_version, settings=settings, activity_log=activity_log)
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(destination)
        return destination

    @staticmethod
    def _safe_settings(settings: dict[str, Any]) -> dict[str, Any]:
        allowed_sections = {"gui", "launch", "updates", "window"}
        safe: dict[str, Any] = {}
        for section, value in settings.items():
            if section not in allowed_sections or not isinstance(value, dict):
                continue
            safe[section] = dict(value)
        geometry = safe.get("window", {}).get("geometry")
        if geometry:
            safe["window"]["geometry"] = "<saved>"
        return safe

    @staticmethod
    def _language_files() -> list[str]:
        roots = [Paths.root() / "lang"]
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass) / "lang")
        found: set[str] = set()
        for root in roots:
            try:
                found.update(path.name for path in root.glob("*.json") if path.is_file())
            except OSError:
                continue
        return sorted(found, key=str.casefold)
