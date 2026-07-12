from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.fs.paths import Paths
from src.core.minecraft.argument_builder import ArgumentBuilder
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.core.minecraft.launcher_manager import LauncherManager


def make_version(
    *,
    main_class: str = "net.minecraft.client.main.Main",
):
    return SimpleNamespace(
        id="1.20.1",
        main_class=main_class,
    )


def make_settings():
    return SimpleNamespace(
        offline_multiplayer_enabled=False,
    )


def make_account():
    return SimpleNamespace(
        account_type="offline",
    )


def test_build_calls_classpath_builder_with_expected_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    version = make_version()
    settings = make_settings()
    account = make_account()
    context = {"classpath": "unused"}
    client_path = tmp_path / "client.jar"
    libraries_path = tmp_path / "libraries"
    received = {}

    monkeypatch.setattr(
        Paths,
        "client",
        lambda received_version: client_path,
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: libraries_path,
    )

    def fake_classpath_build(
        received_version,
        received_client,
        received_libraries,
    ):
        received["version"] = received_version
        received["client"] = received_client
        received["libraries"] = received_libraries
        return "libraries;client.jar"

    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        fake_classpath_build,
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: ([], []),
    )

    LauncherManager.build(
        version=version,
        context=context,
        settings=settings,
        account=account,
    )

    assert received == {
        "version": version,
        "client": client_path,
        "libraries": libraries_path,
    }


def test_build_calls_argument_builder_with_expected_objects(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    version = make_version()
    context = {
        "auth_player_name": "Steve",
    }
    settings = make_settings()
    account = make_account()
    received = {}

    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )

    def fake_argument_build(
        received_version,
        received_context,
        received_settings,
        received_account,
    ):
        received["version"] = received_version
        received["context"] = received_context
        received["settings"] = received_settings
        received["account"] = received_account
        return [], []

    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        fake_argument_build,
    )

    LauncherManager.build(
        version=version,
        context=context,
        settings=settings,
        account=account,
    )

    assert received == {
        "version": version,
        "context": context,
        "settings": settings,
        "account": account,
    }


def test_build_places_jvm_arguments_first(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: (
            [
                "-Xms1G",
                "-Xmx2G",
                "-Dexample=true",
            ],
            [],
        ),
    )

    result = LauncherManager.build(
        version=make_version(),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert result[:3] == [
        "-Xms1G",
        "-Xmx2G",
        "-Dexample=true",
    ]


def test_build_adds_classpath_flag_and_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: (
            "first.jar;second.jar;client.jar"
        ),
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: ([], []),
    )

    result = LauncherManager.build(
        version=make_version(),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert result[:2] == [
        "-cp",
        "first.jar;second.jar;client.jar",
    ]


def test_build_places_main_class_after_classpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: ([], []),
    )

    result = LauncherManager.build(
        version=make_version(
            main_class="example.minecraft.Main"
        ),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert result == [
        "-cp",
        "classpath",
        "example.minecraft.Main",
    ]


def test_build_places_game_arguments_last(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: (
            [],
            [
                "--username",
                "Steve",
                "--version",
                "1.20.1",
            ],
        ),
    )

    result = LauncherManager.build(
        version=make_version(),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert result[-4:] == [
        "--username",
        "Steve",
        "--version",
        "1.20.1",
    ]


def test_build_returns_complete_command_in_correct_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "lib-a.jar;client.jar",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: (
            [
                "-Xms1024M",
                "-Xmx2048M",
            ],
            [
                "--username",
                "Steve",
            ],
        ),
    )

    result = LauncherManager.build(
        version=make_version(),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert result == [
        "-Xms1024M",
        "-Xmx2048M",
        "-cp",
        "lib-a.jar;client.jar",
        "net.minecraft.client.main.Main",
        "--username",
        "Steve",
    ]


def test_build_returns_list_of_strings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: (
            ["-Xmx2G"],
            ["--demo"],
        ),
    )

    result = LauncherManager.build(
        version=make_version(),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert isinstance(result, list)
    assert all(
        isinstance(item, str)
        for item in result
    )


def test_build_supports_empty_jvm_and_game_arguments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: ([], []),
    )

    result = LauncherManager.build(
        version=make_version(
            main_class="Main"
        ),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert result == [
        "-cp",
        "",
        "Main",
    ]


def test_build_does_not_print_debug_information(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    settings = SimpleNamespace(
        offline_multiplayer_enabled=True,
    )
    account = SimpleNamespace(
        account_type="offline",
    )

    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: ([], []),
    )

    LauncherManager.build(
        version=make_version(),
        context={},
        settings=settings,
        account=account,
    )

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_build_does_not_modify_argument_lists(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    jvm_args = [
        "-Xms1G",
        "-Xmx2G",
    ]
    game_args = [
        "--username",
        "Steve",
    ]
    original_jvm = list(jvm_args)
    original_game = list(game_args)

    monkeypatch.setattr(
        Paths,
        "client",
        lambda version: tmp_path / "client.jar",
    )
    monkeypatch.setattr(
        Paths,
        "libraries",
        lambda: tmp_path / "libraries",
    )
    monkeypatch.setattr(
        ClasspathBuilder,
        "build",
        lambda *args: "classpath",
    )
    monkeypatch.setattr(
        ArgumentBuilder,
        "build",
        lambda *args: (
            jvm_args,
            game_args,
        ),
    )

    LauncherManager.build(
        version=make_version(),
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert jvm_args == original_jvm
    assert game_args == original_game