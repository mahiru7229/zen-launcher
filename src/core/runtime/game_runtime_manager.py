from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from src.core.fs.paths import Paths
from src.core.java.java_runtime import JavaRuntime
from src.models.instance.instance import Instance
from src.models.runtime.game_exit_result import GameExitResult


GameExitCallback = Callable[[GameExitResult], None]


class GameRuntimeManager:
    HISTORY_SCHEMA_VERSION = 1
    HISTORY_LIMIT = 50
    POLL_INTERVAL_SECONDS = 0.5

    @classmethod
    def watch(cls, process: object, instance: Instance, minecraft_version: str, started_at: datetime, on_exit: GameExitCallback | None = None) -> bool:
        poll = getattr(process, "poll", None)
        if not callable(poll):
            return False

        watcher = threading.Thread(target=cls._watch_process, args=(process, instance, minecraft_version, started_at, on_exit), name=f"game-runtime-{instance.name}", daemon=True)
        watcher.start()
        return True

    @classmethod
    def _watch_process(cls, process: object, instance: Instance, minecraft_version: str, started_at: datetime, on_exit: GameExitCallback | None) -> None:
        exit_code = cls._wait_for_exit(process)
        ended_at = datetime.now(timezone.utc)
        log_path = JavaRuntime.log_path(process) or cls.latest_game_log(instance)
        JavaRuntime.close_process_log(process)
        crash_report_path = cls.latest_crash_report(instance, since=started_at)
        crashed = exit_code != 0 or crash_report_path is not None
        duration_seconds = max(0, round((ended_at - started_at).total_seconds()))
        pid = getattr(process, "pid", None)
        result = GameExitResult(
            instance_name=instance.name,
            minecraft_version=minecraft_version,
            pid=pid if isinstance(pid, int) and pid > 0 else None,
            exit_code=exit_code,
            started_at=started_at.isoformat(),
            ended_at=ended_at.isoformat(),
            duration_seconds=duration_seconds,
            crashed=crashed,
            log_path=log_path,
            crash_report_path=crash_report_path,
        )
        try:
            cls._record_result(instance, result)
        finally:
            if on_exit is not None:
                try:
                    on_exit(result)
                except Exception:
                    pass

    @classmethod
    def _wait_for_exit(cls, process: object) -> int:
        poll = getattr(process, "poll", None)
        if not callable(poll):
            return -1
        while True:
            try:
                result = poll()
            except Exception:
                return -1
            if result is not None:
                try:
                    return int(result)
                except (TypeError, ValueError):
                    return -1
            time.sleep(cls.POLL_INTERVAL_SECONDS)

    @staticmethod
    def latest_game_log(instance: Instance) -> Path | None:
        return GameRuntimeManager._latest_file(Paths.instance_logs_dir(instance), "minecraft-*.log")

    @staticmethod
    def latest_crash_report(instance: Instance, since: datetime | None = None) -> Path | None:
        path = GameRuntimeManager._latest_file(Paths.instance_crash_reports_dir(instance), "*.txt")
        if path is None or since is None:
            return path
        try:
            return path if path.stat().st_mtime >= since.timestamp() - 2.0 else None
        except OSError:
            return None

    @staticmethod
    def _latest_file(directory: Path, pattern: str) -> Path | None:
        try:
            files = [path for path in directory.glob(pattern) if path.is_file()]
        except OSError:
            return None
        if not files:
            return None
        try:
            return max(files, key=lambda path: path.stat().st_mtime)
        except OSError:
            return sorted(files, key=lambda path: path.name.casefold())[-1]

    @classmethod
    def _record_result(cls, instance: Instance, result: GameExitResult) -> None:
        try:
            cls._append_history(instance, result)
        except OSError:
            pass
        try:
            cls._update_instance_metadata(instance, result)
        except OSError:
            pass

    @classmethod
    def _append_history(cls, instance: Instance, result: GameExitResult) -> None:
        path = Paths.instance_runtime_history(instance)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, json.JSONDecodeError, ValueError):
            data = {}
        records = data.get("records") if isinstance(data, dict) else None
        if not isinstance(records, list):
            records = []
        records.append(result.to_dict())
        payload = {"schema_version": cls.HISTORY_SCHEMA_VERSION, "records": records[-cls.HISTORY_LIMIT:]}
        cls._write_json_atomic(path, payload)

    @classmethod
    def _update_instance_metadata(cls, instance: Instance, result: GameExitResult) -> None:
        path = Paths.instance_metadata(instance.name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            return
        if not isinstance(data, dict):
            return
        previous_play_time = data.get("total_play_time_seconds", 0)
        try:
            total_play_time = max(0, int(previous_play_time)) + result.duration_seconds
        except (TypeError, ValueError):
            total_play_time = result.duration_seconds
        data.update({
            "updated_at": result.ended_at,
            "last_played": result.ended_at,
            "total_play_time_seconds": total_play_time,
            "last_exit_code": result.exit_code,
            "last_launch_crashed": result.crashed,
            "last_game_log": str(result.log_path) if result.log_path is not None else "",
            "last_crash_report": str(result.crash_report_path) if result.crash_report_path is not None else "",
        })
        cls._write_json_atomic(path, data)

    @staticmethod
    def _write_json_atomic(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.tmp")
        payload = json.dumps(data, indent=4, ensure_ascii=False) + "\n"
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
