import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.fs.paths import Paths
from src.core.java.java_runtime import JavaRuntime
from src.core.runtime.game_runtime_manager import GameRuntimeManager


class FinishedProcess:
    def __init__(self, exit_code: int, pid: int = 43210) -> None:
        self.pid = pid
        self.returncode = exit_code

    def poll(self) -> int:
        return self.returncode


@pytest.fixture
def instance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    instance_dir = tmp_path / "instances" / "Runtime Test"
    instance_dir.mkdir(parents=True)
    metadata = {
        "id": "runtime-test",
        "name": "Runtime Test",
        "version_id": "1.21.1",
        "mod_loader": ["vanilla", "-1"],
        "instance_dir": str(instance_dir),
        "notes": "keep this field",
    }
    (instance_dir / "instance.json").write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(Paths, "load_instance_dir", lambda name: instance_dir)
    return SimpleNamespace(name="Runtime Test", instance_dir=instance_dir)


def test_watch_process_records_normal_exit(monkeypatch: pytest.MonkeyPatch, instance) -> None:
    started_at = datetime.now(timezone.utc) - timedelta(seconds=65)
    log_path = Path(instance.instance_dir) / "logs" / "minecraft-test.log"
    log_path.parent.mkdir(parents=True)
    log_path.write_text("game output", encoding="utf-8")
    closed = []
    results = []

    monkeypatch.setattr(JavaRuntime, "log_path", classmethod(lambda cls, process: log_path))
    monkeypatch.setattr(JavaRuntime, "close_process_log", classmethod(lambda cls, process: closed.append(process.pid)))

    GameRuntimeManager._watch_process(FinishedProcess(0), instance, "1.21.1", started_at, results.append)

    assert len(results) == 1
    result = results[0]
    assert result.exit_code == 0
    assert result.crashed is False
    assert result.duration_seconds >= 60
    assert result.log_path == log_path
    assert closed == [43210]

    history = json.loads(Paths.instance_runtime_history(instance).read_text(encoding="utf-8"))
    assert history["records"][-1]["exit_code"] == 0

    metadata = json.loads(Paths.instance_metadata(instance.name).read_text(encoding="utf-8"))
    assert metadata["notes"] == "keep this field"
    assert metadata["last_launch_crashed"] is False
    assert metadata["total_play_time_seconds"] >= 60


def test_new_crash_report_marks_zero_exit_as_crash(monkeypatch: pytest.MonkeyPatch, instance) -> None:
    started_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    crash_dir = Paths.instance_crash_reports_dir(instance)
    crash_report = crash_dir / "crash-2026-07-15.txt"
    crash_report.write_text("crash", encoding="utf-8")
    results = []

    monkeypatch.setattr(JavaRuntime, "log_path", classmethod(lambda cls, process: None))
    monkeypatch.setattr(JavaRuntime, "close_process_log", classmethod(lambda cls, process: None))

    GameRuntimeManager._watch_process(FinishedProcess(0), instance, "1.21.1", started_at, results.append)

    assert results[0].crashed is True
    assert results[0].crash_report_path == crash_report


def test_nonzero_exit_is_crash_without_report(monkeypatch: pytest.MonkeyPatch, instance) -> None:
    results = []
    monkeypatch.setattr(JavaRuntime, "log_path", classmethod(lambda cls, process: None))
    monkeypatch.setattr(JavaRuntime, "close_process_log", classmethod(lambda cls, process: None))

    GameRuntimeManager._watch_process(FinishedProcess(1), instance, "1.21.1", datetime.now(timezone.utc), results.append)

    assert results[0].crashed is True
    assert results[0].exit_code == 1
    assert results[0].crash_report_path is None


def test_watch_rejects_object_without_poll(instance) -> None:
    assert GameRuntimeManager.watch(object(), instance, "1.21.1", datetime.now(timezone.utc)) is False


def test_callback_still_runs_when_runtime_history_cannot_be_written(monkeypatch: pytest.MonkeyPatch, instance) -> None:
    results = []
    monkeypatch.setattr(JavaRuntime, "log_path", classmethod(lambda cls, process: None))
    monkeypatch.setattr(JavaRuntime, "close_process_log", classmethod(lambda cls, process: None))
    monkeypatch.setattr(GameRuntimeManager, "_append_history", classmethod(lambda cls, received_instance, result: (_ for _ in ()).throw(OSError("disk full"))))
    monkeypatch.setattr(GameRuntimeManager, "_update_instance_metadata", classmethod(lambda cls, received_instance, result: None))

    GameRuntimeManager._watch_process(FinishedProcess(0), instance, "1.21.1", datetime.now(timezone.utc), results.append)

    assert len(results) == 1
    assert results[0].exit_code == 0
