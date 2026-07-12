from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.fs.paths import Paths
from src.core.instance.settings_manager import SettingsManager
from src.core.java.java_runtime import JavaRuntime
from src.core.java.java_selector import JavaSelector
from src.core.minecraft.asset_manager import AssetManager
from src.core.minecraft.context_builder import ContextBuilder
from src.core.minecraft.download_manager import DownloadClientManager
from src.core.minecraft.launcher_manager import LauncherManager
from src.core.minecraft.library_manager import DownloadLibraryManager
from src.core.minecraft.minecraft_executor import MinecraftExecutor
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.version_manifest_manager import (
    VersionManifestManager,
)
from src.models.progress.progress_stage import ProgressStage


def make_instance(
    *,
    version_id: str = "1.20.1",
):
    return SimpleNamespace(
        name="Test Instance",
        version_id=version_id,
    )


def make_version(
    *,
    version_id: str = "1.20.1",
    java_version: dict | None = None,
):
    return SimpleNamespace(
        id=version_id,
        java_version=(
            {"majorVersion": 17}
            if java_version is None
            else java_version
        ),
    )


def patch_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    *,
    version=None,
    java_path: Path | None = None,
):
    version = version or make_version()
    java_path = java_path or Path(
        "C:/Java/bin/javaw.exe"
    )

    settings = object()
    context = {
        "classpath": "libraries;client.jar",
    }
    command = [
        "-Xmx2G",
        "-cp",
        "libraries;client.jar",
        "net.minecraft.client.main.Main",
    ]

    monkeypatch.setattr(
        VersionManifestManager,
        "get",
        lambda: [],
    )
    monkeypatch.setattr(
        VersionManager,
        "load",
        lambda version_id: version,
    )
    monkeypatch.setattr(
        DownloadClientManager,
        "load",
        lambda **kwargs: Path("client.jar"),
    )
    monkeypatch.setattr(
        DownloadLibraryManager,
        "load",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        AssetManager,
        "load",
        lambda **kwargs: Path("assets"),
    )
    monkeypatch.setattr(
        SettingsManager,
        "load",
        lambda instance: settings,
    )
    monkeypatch.setattr(
        ContextBuilder,
        "build",
        lambda instance, version, authentication: context,
    )
    monkeypatch.setattr(
        LauncherManager,
        "build",
        lambda version, context, settings, account: command,
    )
    monkeypatch.setattr(
        JavaSelector,
        "select_java",
        lambda major: java_path,
    )
    monkeypatch.setattr(
        JavaRuntime,
        "run",
        lambda java, command, instance: object(),
    )

    return {
        "version": version,
        "java_path": java_path,
        "settings": settings,
        "context": context,
        "command": command,
    }


def test_run_returns_launch_information(
    monkeypatch: pytest.MonkeyPatch,
):
    pipeline = patch_pipeline(monkeypatch)

    result = MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
    )

    assert result == {
        "javaPath": pipeline["java_path"],
        "minecraftJavaMajorVersion": 17,
        "minecraftVersion": "1.20.1",
    }


def test_run_calls_pipeline_in_expected_order(
    monkeypatch: pytest.MonkeyPatch,
):
    instance = make_instance()
    authentication = object()
    account = object()
    version = make_version()
    settings = object()
    context = object()
    command = ["command"]
    java_path = Path("javaw.exe")
    calls = []

    monkeypatch.setattr(
        VersionManifestManager,
        "get",
        lambda: calls.append(("manifest",)),
    )

    def load_version(version_id):
        calls.append(("version", version_id))
        return version

    monkeypatch.setattr(
        VersionManager,
        "load",
        load_version,
    )

    def load_client(**kwargs):
        calls.append(
            (
                "client",
                kwargs["version"],
                kwargs["reporter"],
            )
        )

    monkeypatch.setattr(
        DownloadClientManager,
        "load",
        load_client,
    )

    def load_libraries(**kwargs):
        calls.append(
            (
                "libraries",
                kwargs["version"],
                kwargs["reporter"],
            )
        )

    monkeypatch.setattr(
        DownloadLibraryManager,
        "load",
        load_libraries,
    )

    def load_assets(**kwargs):
        calls.append(
            (
                "assets",
                kwargs["version"],
                kwargs["reporter"],
            )
        )

    monkeypatch.setattr(
        AssetManager,
        "load",
        load_assets,
    )

    def load_settings(received_instance):
        calls.append(
            ("settings", received_instance)
        )
        return settings

    monkeypatch.setattr(
        SettingsManager,
        "load",
        load_settings,
    )

    def build_context(
        received_instance,
        received_version,
        received_authentication,
    ):
        calls.append(
            (
                "context",
                received_instance,
                received_version,
                received_authentication,
            )
        )
        return context

    monkeypatch.setattr(
        ContextBuilder,
        "build",
        build_context,
    )

    def build_command(
        received_version,
        received_context,
        received_settings,
        received_account,
    ):
        calls.append(
            (
                "command",
                received_version,
                received_context,
                received_settings,
                received_account,
            )
        )
        return command

    monkeypatch.setattr(
        LauncherManager,
        "build",
        build_command,
    )

    def select_java(major):
        calls.append(("java", major))
        return java_path

    monkeypatch.setattr(
        JavaSelector,
        "select_java",
        select_java,
    )

    def run_java(
        received_java,
        received_command,
        received_instance,
    ):
        calls.append(
            (
                "launch",
                received_java,
                received_command,
                received_instance,
            )
        )

    monkeypatch.setattr(
        JavaRuntime,
        "run",
        run_java,
    )

    MinecraftExecutor.run(
        instance=instance,
        authentication=authentication,
        account=account,
    )

    assert [
        call[0]
        for call in calls
    ] == [
        "manifest",
        "version",
        "client",
        "libraries",
        "assets",
        "settings",
        "context",
        "command",
        "java",
        "launch",
    ]

    assert calls[1] == (
        "version",
        "1.20.1",
    )
    assert calls[-1] == (
        "launch",
        java_path,
        command,
        instance,
    )


def test_run_passes_same_reporter_to_download_managers(
    monkeypatch: pytest.MonkeyPatch,
):
    version = make_version()
    reporters = []

    monkeypatch.setattr(
        VersionManifestManager,
        "get",
        lambda: [],
    )
    monkeypatch.setattr(
        VersionManager,
        "load",
        lambda version_id: version,
    )

    def capture_reporter(**kwargs):
        reporters.append(kwargs["reporter"])

    monkeypatch.setattr(
        DownloadClientManager,
        "load",
        capture_reporter,
    )
    monkeypatch.setattr(
        DownloadLibraryManager,
        "load",
        capture_reporter,
    )
    monkeypatch.setattr(
        AssetManager,
        "load",
        capture_reporter,
    )
    monkeypatch.setattr(
        SettingsManager,
        "load",
        lambda instance: object(),
    )
    monkeypatch.setattr(
        ContextBuilder,
        "build",
        lambda *args: {},
    )
    monkeypatch.setattr(
        LauncherManager,
        "build",
        lambda *args: [],
    )
    monkeypatch.setattr(
        JavaSelector,
        "select_java",
        lambda major: Path("javaw.exe"),
    )
    monkeypatch.setattr(
        JavaRuntime,
        "run",
        lambda *args: None,
    )

    MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
    )

    assert len(reporters) == 3
    assert reporters[0] is reporters[1]
    assert reporters[1] is reporters[2]


def test_run_emits_progress_stages_in_expected_order(
    monkeypatch: pytest.MonkeyPatch,
):
    patch_pipeline(monkeypatch)
    events = []

    MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
        on_progress=events.append,
    )

    assert [
        event.stage
        for event in events
    ] == [
        ProgressStage.PREPARING,
        ProgressStage.LOADING_VERSION,
        ProgressStage.DOWNLOADING_CLIENT,
        ProgressStage.DOWNLOADING_LIBRARIES,
        ProgressStage.DOWNLOADING_ASSETS,
        ProgressStage.BUILDING_CONTEXT,
        ProgressStage.BUILDING_COMMAND,
        ProgressStage.SELECTING_JAVA,
        ProgressStage.LAUNCHING,
        ProgressStage.FINISHED,
    ]


def test_run_emits_expected_progress_messages(
    monkeypatch: pytest.MonkeyPatch,
):
    patch_pipeline(monkeypatch)
    events = []

    MinecraftExecutor.run(
        instance=make_instance(
            version_id="1.20.1"
        ),
        authentication=object(),
        account=object(),
        on_progress=events.append,
    )

    assert [
        event.message
        for event in events
    ] == [
        "Preparing Minecraft...",
        "Loading Minecraft 1.20.1...",
        "Checking Minecraft client...",
        "Checking Minecraft libraries...",
        "Checking Minecraft assets...",
        "Building launch context...",
        "Building launch command...",
        "Selecting Java runtime...",
        "Launching Minecraft 1.20.1...",
        (
            "Minecraft 1.20.1 "
            "launched successfully."
        ),
    ]


def test_run_uses_required_java_major_version(
    monkeypatch: pytest.MonkeyPatch,
):
    version = make_version(
        java_version={
            "majorVersion": 21
        }
    )
    selected = []

    patch_pipeline(
        monkeypatch,
        version=version,
    )
    monkeypatch.setattr(
        JavaSelector,
        "select_java",
        lambda major: (
            selected.append(major)
            or Path("java21/javaw.exe")
        ),
    )

    result = MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
    )

    assert selected == [21]
    assert (
        result["minecraftJavaMajorVersion"]
        == 21
    )


def test_run_defaults_to_java_8_when_major_version_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    version = make_version(
        java_version={}
    )
    selected = []

    patch_pipeline(
        monkeypatch,
        version=version,
    )
    monkeypatch.setattr(
        JavaSelector,
        "select_java",
        lambda major: (
            selected.append(major)
            or Path("java8/javaw.exe")
        ),
    )

    result = MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
    )

    assert selected == [8]
    assert (
        result["minecraftJavaMajorVersion"]
        == 8
    )


def test_run_passes_authentication_to_context_builder(
    monkeypatch: pytest.MonkeyPatch,
):
    instance = make_instance()
    authentication = object()
    account = object()
    version = make_version()
    received = {}

    patch_pipeline(
        monkeypatch,
        version=version,
    )

    def fake_build(
        received_instance,
        received_version,
        received_authentication,
    ):
        received.update(
            {
                "instance": received_instance,
                "version": received_version,
                "authentication": (
                    received_authentication
                ),
            }
        )
        return {}

    monkeypatch.setattr(
        ContextBuilder,
        "build",
        fake_build,
    )

    MinecraftExecutor.run(
        instance=instance,
        authentication=authentication,
        account=account,
    )

    assert received == {
        "instance": instance,
        "version": version,
        "authentication": authentication,
    }


def test_run_passes_account_to_launcher_manager(
    monkeypatch: pytest.MonkeyPatch,
):
    account = object()
    received = {}

    pipeline = patch_pipeline(monkeypatch)

    def fake_build(
        version,
        context,
        settings,
        received_account,
    ):
        received["account"] = received_account
        return pipeline["command"]

    monkeypatch.setattr(
        LauncherManager,
        "build",
        fake_build,
    )

    MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=account,
    )

    assert received["account"] is account


def test_run_passes_selected_java_command_and_instance_to_runtime(
    monkeypatch: pytest.MonkeyPatch,
):
    instance = make_instance()
    java_path = Path(
        "C:/Java/bin/javaw.exe"
    )
    pipeline = patch_pipeline(
        monkeypatch,
        java_path=java_path,
    )
    received = {}

    def fake_run(
        java,
        command,
        received_instance,
    ):
        received.update(
            {
                "java": java,
                "command": command,
                "instance": received_instance,
            }
        )

    monkeypatch.setattr(
        JavaRuntime,
        "run",
        fake_run,
    )

    MinecraftExecutor.run(
        instance=instance,
        authentication=object(),
        account=object(),
    )

    assert received == {
        "java": java_path,
        "command": pipeline["command"],
        "instance": instance,
    }


def test_run_does_not_print_debug_information_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    patch_pipeline(monkeypatch)

    MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
    )

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_run_prints_native_debug_information_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    version = make_version()
    patch_pipeline(
        monkeypatch,
        version=version,
    )

    native_dir = tmp_path / "natives"
    native_dir.mkdir()
    native_file = native_dir / "lwjgl.dll"
    native_file.write_bytes(b"native")

    monkeypatch.setattr(
        Paths,
        "natives",
        lambda received_version: native_dir,
    )

    MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
        debug_mode=True,
    )

    output = capsys.readouterr().out

    assert (
        f"Native directory: {native_dir}"
        in output
    )
    assert "Exists: True" in output
    assert "lwjgl.dll" in output


def test_run_debug_mode_handles_missing_native_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    patch_pipeline(monkeypatch)

    native_dir = (
        tmp_path
        / "missing-natives"
    )

    monkeypatch.setattr(
        Paths,
        "natives",
        lambda version: native_dir,
    )

    MinecraftExecutor.run(
        instance=make_instance(),
        authentication=object(),
        account=object(),
        debug_mode=True,
    )

    output = capsys.readouterr().out

    assert (
        f"Native directory: {native_dir}"
        in output
    )
    assert "Exists: False" in output
    assert "Native files:" not in output


def test_run_propagates_pipeline_exception_and_does_not_emit_finished(
    monkeypatch: pytest.MonkeyPatch,
):
    patch_pipeline(monkeypatch)
    events = []
    expected_error = RuntimeError(
        "library download failed"
    )

    def fail_libraries(**kwargs):
        raise expected_error

    monkeypatch.setattr(
        DownloadLibraryManager,
        "load",
        fail_libraries,
    )

    with pytest.raises(RuntimeError) as error:
        MinecraftExecutor.run(
            instance=make_instance(),
            authentication=object(),
            account=object(),
            on_progress=events.append,
        )

    assert error.value is expected_error
    assert (
        ProgressStage.FINISHED
        not in [
            event.stage
            for event in events
        ]
    )
    assert [
        event.stage
        for event in events
    ][-1] is (
        ProgressStage.DOWNLOADING_LIBRARIES
    )