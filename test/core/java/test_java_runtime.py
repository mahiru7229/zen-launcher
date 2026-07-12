from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.fs.paths import Paths
from src.core.java.java_runtime import JavaRuntime


class FixedDateTime:
    @classmethod
    def now(cls):
        return cls()

    def strftime(self, format_string: str) -> str:
        assert format_string == "%Y-%m-%d_%H-%M-%S"
        return "2026-07-12_14-30-45"


@pytest.fixture
def instance():
    return SimpleNamespace(
        name="Test Instance"
    )


@pytest.fixture
def instance_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Path:
    path = tmp_path / "instances" / "Test Instance"

    monkeypatch.setattr(
        Paths,
        "load_instance_dir",
        lambda name: path,
    )

    return path


def test_run_returns_process_from_popen(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    expected_process = object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        lambda *args, **kwargs: expected_process,
    )

    result = JavaRuntime.run(
        java=Path("C:/Java/bin/javaw.exe"),
        command=["-version"],
        instance=instance,
    )

    assert result is expected_process


def test_run_builds_command_with_java_first(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    def fake_popen(command, **kwargs):
        received["command"] = command
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("C:/Java/bin/javaw.exe"),
        command=[
            "-Xmx2G",
            "-cp",
            "libraries;client.jar",
            "net.minecraft.client.main.Main",
        ],
        instance=instance,
    )

    assert received["command"] == [
        str(Path("C:/Java/bin/javaw.exe")),
        "-Xmx2G",
        "-cp",
        "libraries;client.jar",
        "net.minecraft.client.main.Main",
    ]


def test_run_uses_instance_directory_as_cwd(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    def fake_popen(command, **kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    assert received["cwd"] == instance_dir


def test_run_resolves_instance_directory_by_name(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    received_names = []
    expected_dir = tmp_path / "instances" / "Named Instance"
    instance = SimpleNamespace(
        name="Named Instance",
        instance_dir=tmp_path / "ignored-directory",
    )

    def fake_load_instance_dir(name: str) -> Path:
        received_names.append(name)
        return expected_dir

    monkeypatch.setattr(
        Paths,
        "load_instance_dir",
        fake_load_instance_dir,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        lambda *args, **kwargs: object(),
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    assert received_names == [
        "Named Instance",
        "Named Instance",
    ]


def test_run_creates_logs_directory(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        lambda *args, **kwargs: object(),
    )

    logs_dir = instance_dir / "logs"

    assert not logs_dir.exists()

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    assert logs_dir.exists()
    assert logs_dir.is_dir()


def test_run_creates_timestamped_log_file(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        lambda *args, **kwargs: object(),
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    expected_log = (
        instance_dir
        / "logs"
        / "minecraft-2026-07-12_14-30-45.log"
    )

    assert expected_log.exists()
    assert expected_log.is_file()


def test_run_redirects_stdout_to_log_file(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    def fake_popen(command, **kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    log_file = received["stdout"]

    assert log_file.name.endswith(
        "minecraft-2026-07-12_14-30-45.log"
    )
    assert log_file.mode == "w"
    assert log_file.encoding.lower().replace("-", "") == "utf8"


def test_run_redirects_stderr_to_stdout(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    def fake_popen(command, **kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    from src.core.java import java_runtime

    assert (
        received["stderr"]
        is java_runtime.subprocess.STDOUT
    )


def test_run_disables_standard_input(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    def fake_popen(command, **kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    from src.core.java import java_runtime

    assert (
        received["stdin"]
        is java_runtime.subprocess.DEVNULL
    )


def test_run_uses_create_no_window_on_windows(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.os.name",
        "nt",
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )

    def fake_popen(command, **kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("javaw.exe"),
        command=[],
        instance=instance,
    )

    assert received["creationflags"] == 0x08000000


def test_run_uses_zero_creation_flags_outside_windows(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.os.name",
        "posix",
    )

    def fake_popen(command, **kwargs):
        received.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("java"),
        command=[],
        instance=instance,
    )

    assert received["creationflags"] == 0


def test_run_closes_log_file_when_popen_fails(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    def failing_popen(command, **kwargs):
        received.update(kwargs)
        raise OSError("cannot start Java")

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        failing_popen,
    )

    with pytest.raises(
        OSError,
        match="cannot start Java",
    ):
        JavaRuntime.run(
            java=Path("javaw.exe"),
            command=[],
            instance=instance,
        )

    assert received["stdout"].closed is True


def test_run_does_not_swallow_popen_exception(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )

    expected_error = PermissionError(
        "Java executable is not permitted"
    )

    def failing_popen(*args, **kwargs):
        raise expected_error

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        failing_popen,
    )

    with pytest.raises(PermissionError) as error:
        JavaRuntime.run(
            java=Path("javaw.exe"),
            command=[],
            instance=instance,
        )

    assert error.value is expected_error


def test_run_passes_all_expected_popen_options(
    monkeypatch: pytest.MonkeyPatch,
    instance,
    instance_dir: Path,
):
    received = {}

    monkeypatch.setattr(
        "src.core.java.java_runtime.datetime",
        FixedDateTime,
    )
    monkeypatch.setattr(
        "src.core.java.java_runtime.os.name",
        "posix",
    )

    def fake_popen(command, **kwargs):
        received["command"] = command
        received["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(
        "src.core.java.java_runtime.subprocess.Popen",
        fake_popen,
    )

    JavaRuntime.run(
        java=Path("java"),
        command=["-version"],
        instance=instance,
    )

    from src.core.java import java_runtime

    assert received["command"] == [
        "java",
        "-version",
    ]
    assert set(received["kwargs"]) == {
        "cwd",
        "stdin",
        "stdout",
        "stderr",
        "creationflags",
    }
    assert received["kwargs"]["cwd"] == instance_dir
    assert (
        received["kwargs"]["stdin"]
        is java_runtime.subprocess.DEVNULL
    )
    assert (
        received["kwargs"]["stderr"]
        is java_runtime.subprocess.STDOUT
    )
    assert received["kwargs"]["creationflags"] == 0