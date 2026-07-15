from pathlib import Path
from types import SimpleNamespace

from src.core.diagnostics.diagnostics_manager import DiagnosticsManager
from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager
from src.core.instance.instance_run_lock import InstanceRunLock


def test_build_report_contains_safe_runtime_information(tmp_path, monkeypatch):
    monkeypatch.setattr(Paths, "CONFIG_ROOT", tmp_path / "config")
    monkeypatch.setattr(Paths, "INSTANCES_ROOT", tmp_path / "instances")
    monkeypatch.setattr(Paths, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(Paths, "ACCOUNTS_ROOT", tmp_path / "accounts")
    monkeypatch.setattr(Paths, "LOGS_ROOT", tmp_path / "logs")
    monkeypatch.setattr(InstanceManager, "list_instances", lambda: [SimpleNamespace(name="One")])
    monkeypatch.setattr(InstanceRunLock, "list_active", lambda: [SimpleNamespace(name="One", state="running", minecraft_pid=123, launcher_pid=10)])

    report = DiagnosticsManager.build_report("0.5.0-beta.3", settings={"gui": {"language": "vi-VN"}, "secret": {"token": "nope"}}, activity_log="hello")

    assert "launcher_version: 0.5.0-beta.3" in report
    assert "running_instance: One [running] pid=123" in report
    assert '"language": "vi-VN"' in report
    assert "token" not in report
    assert "hello" in report


def test_write_report_is_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(InstanceManager, "list_instances", lambda: [])
    monkeypatch.setattr(InstanceRunLock, "list_active", lambda: [])
    destination = tmp_path / "diagnostics.txt"

    result = DiagnosticsManager.write_report(destination, "0.5.0-beta.3")

    assert result == destination
    assert destination.is_file()
    assert not destination.with_name("diagnostics.txt.tmp").exists()


def test_build_report_redacts_tokens_from_activity_log(tmp_path, monkeypatch):
    monkeypatch.setattr(Paths, "CONFIG_ROOT", tmp_path / "config")
    monkeypatch.setattr(Paths, "INSTANCES_ROOT", tmp_path / "instances")
    monkeypatch.setattr(Paths, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(Paths, "ACCOUNTS_ROOT", tmp_path / "accounts")
    monkeypatch.setattr(Paths, "LOGS_ROOT", tmp_path / "logs")
    monkeypatch.setattr(InstanceManager, "list_instances", lambda: [])
    monkeypatch.setattr(InstanceRunLock, "list_active", lambda: [])

    report = DiagnosticsManager.build_report(
        "0.5.0-beta.10",
        activity_log="Authorization: Bearer secret-token refresh_token=refresh-secret&code=oauth-code",
    )

    assert "secret-token" not in report
    assert "refresh-secret" not in report
    assert "oauth-code" not in report
    assert "<redacted>" in report
