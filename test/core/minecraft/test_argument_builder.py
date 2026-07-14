from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.minecraft.argument_builder import ArgumentBuilder
from src.models.account.account_source import AccountSource
from src.models.instance.settings import InstanceSettings


def make_version(
    *,
    jvm_arguments: list | None = None,
    game_arguments: list | None = None,
):
    return SimpleNamespace(
        arguments={
            "jvm": jvm_arguments or [],
            "game": game_arguments or [],
        }
    )


def make_settings(
    *,
    min_memory: int = 1024,
    max_memory: int = 2048,
    jvm_arguments: list[str] | None = None,
    game_arguments: list[str] | None = None,
    offline_multiplayer_enabled: bool = False,
    width: int = 854,
    height: int = 480,
    fullscreen: bool = False,
) -> InstanceSettings:
    return InstanceSettings(
        java_path=Path("javaw.exe"),
        min_memory=min_memory,
        max_memory=max_memory,
        jvm_arguments=jvm_arguments or [],
        game_arguments=game_arguments or [],
        offline_multiplayer_enabled=offline_multiplayer_enabled,
        width=width,
        height=height,
        fullscreen=fullscreen,
    )


def make_account(
    account_type: AccountSource = AccountSource.OFFLINE
):
    return SimpleNamespace(
        account_type=account_type
    )


def test_build_adds_memory_arguments():
    version = make_version()
    settings = make_settings(
        min_memory=512,
        max_memory=4096,
    )

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert jvm_args[:2] == [
        "-Xms512M",
        "-Xmx4096M",
    ]


def test_build_adds_custom_jvm_arguments_after_memory():
    version = make_version()
    settings = make_settings(
        jvm_arguments=[
            "-XX:+UseG1GC",
            "-Dexample=true",
        ]
    )

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert jvm_args == [
        "-Xms1024M",
        "-Xmx2048M",
        "-XX:+UseG1GC",
        "-Dexample=true",
    ]


def test_build_adds_window_size_arguments():
    version = make_version()
    settings = make_settings(
        width=1280,
        height=720,
    )

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert game_args[:4] == [
        "--width",
        "1280",
        "--height",
        "720",
    ]


def test_build_adds_fullscreen_when_enabled():
    version = make_version()
    settings = make_settings(
        fullscreen=True
    )

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert "--fullscreen" in game_args


def test_build_does_not_add_fullscreen_when_disabled():
    version = make_version()
    settings = make_settings(
        fullscreen=False
    )

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert "--fullscreen" not in game_args


def test_build_adds_custom_game_arguments_after_window_settings():
    version = make_version()
    settings = make_settings(
        game_arguments=[
            "--demo",
            "--quickPlaySingleplayer",
            "Test World",
        ]
    )

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert game_args == [
        "--width",
        "854",
        "--height",
        "480",
        "--demo",
        "--quickPlaySingleplayer",
        "Test World",
    ]


def test_build_resolves_jvm_placeholders():
    version = make_version(
        jvm_arguments=[
            "-Djava.library.path=${natives_directory}",
            "-cp",
            "${classpath}",
        ]
    )
    settings = make_settings()

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={
            "natives_directory": "cache/natives/1.20.1",
            "classpath": "a.jar;b.jar",
        },
        settings=settings,
        account=make_account(),
    )

    assert "-Djava.library.path=cache/natives/1.20.1" in jvm_args
    assert "a.jar;b.jar" in jvm_args


def test_build_resolves_game_placeholders():
    version = make_version(
        game_arguments=[
            "--username",
            "${auth_player_name}",
            "--version",
            "${version_name}",
        ]
    )
    settings = make_settings()

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={
            "auth_player_name": "Steve",
            "version_name": "1.20.1",
        },
        settings=settings,
        account=make_account(),
    )

    assert game_args[-4:] == [
        "--username",
        "Steve",
        "--version",
        "1.20.1",
    ]


def test_build_keeps_unknown_placeholder_unchanged():
    version = make_version(
        game_arguments=[
            "${unknown_value}"
        ]
    )

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert game_args[-1] == "${unknown_value}"


def test_build_supports_rule_based_jvm_entries():
    version = make_version(
        jvm_arguments=[
            {
                "rules": [
                    {"action": "allow"}
                ],
                "value": "-Dexample=true",
            }
        ]
    )

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert "-Dexample=true" in jvm_args
    assert all(
        isinstance(argument, str)
        for argument in jvm_args
    )


def test_build_supports_rule_based_game_entries():
    version = make_version(
        game_arguments=[
            {
                "rules": [
                    {"action": "allow"}
                ],
                "value": "--demo",
            }
        ]
    )

    _, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert "--demo" in game_args
    assert all(
        isinstance(argument, str)
        for argument in game_args
    )


def test_offline_multiplayer_arguments_are_added_for_offline_account():
    version = make_version()
    settings = make_settings(
        offline_multiplayer_enabled=True
    )

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(
            AccountSource.OFFLINE
        ),
    )

    for argument in ArgumentBuilder.OFFLINE_MULTIPLAYER_ARGUMENTS:
        assert argument in jvm_args


def test_offline_multiplayer_arguments_are_not_added_when_disabled():
    version = make_version()
    settings = make_settings(
        offline_multiplayer_enabled=False
    )

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(
            AccountSource.OFFLINE
        ),
    )

    for argument in ArgumentBuilder.OFFLINE_MULTIPLAYER_ARGUMENTS:
        assert argument not in jvm_args


def test_offline_multiplayer_arguments_are_not_added_for_microsoft_account():
    version = make_version()
    settings = make_settings(
        offline_multiplayer_enabled=True
    )

    jvm_args, _ = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(
            AccountSource.MICROSOFT
        ),
    )

    for argument in ArgumentBuilder.OFFLINE_MULTIPLAYER_ARGUMENTS:
        assert argument not in jvm_args


@pytest.mark.parametrize(
    (
        "value",
        "context",
        "expected",
    ),
    [
        (
            "${first}-${second}",
            {
                "first": "alpha",
                "second": "beta",
            },
            "alpha-beta",
        ),
        (
            "${number}",
            {
                "number": 21,
            },
            "21",
        ),
        (
            "plain-value",
            {
                "unused": "value",
            },
            "plain-value",
        ),
        (
            "${same}/${same}",
            {
                "same": "path",
            },
            "path/path",
        ),
    ],
)
def test_resolve_replaces_context_values(
    value: str,
    context: dict,
    expected: str,
):
    assert ArgumentBuilder.resolve(
        value,
        context,
    ) == expected


def test_build_preserves_argument_order():
    version = make_version(
        jvm_arguments=[
            "-Dversion.jvm=1",
            "-Dversion.jvm=2",
        ],
        game_arguments=[
            "--version-game-one",
            "--version-game-two",
        ],
    )
    settings = make_settings(
        jvm_arguments=[
            "-Dsettings.jvm=1",
            "-Dsettings.jvm=2",
        ],
        game_arguments=[
            "--settings-game-one",
            "--settings-game-two",
        ],
        fullscreen=True,
    )

    jvm_args, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=settings,
        account=make_account(),
    )

    assert jvm_args == [
        "-Xms1024M",
        "-Xmx2048M",
        "-Dsettings.jvm=1",
        "-Dsettings.jvm=2",
        "-Dversion.jvm=1",
        "-Dversion.jvm=2",
    ]

    assert game_args == [
        "--width",
        "854",
        "--height",
        "480",
        "--fullscreen",
        "--settings-game-one",
        "--settings-game-two",
        "--version-game-one",
        "--version-game-two",
    ]


def test_build_accepts_version_with_no_arguments():
    version = SimpleNamespace(
        arguments=None
    )

    jvm_args, game_args = ArgumentBuilder.build(
        version=version,
        context={},
        settings=make_settings(),
        account=make_account(),
    )

    assert jvm_args == [
        "-Xms1024M",
        "-Xmx2048M",
    ]
    assert game_args == [
        "--width",
        "854",
        "--height",
        "480",
    ]

def test_build_rejects_rule_based_entry_when_feature_is_disabled():
    version = make_version(
        game_arguments=[
            {
                "rules": [
                    {"action": "allow", "features": {"is_demo_user": True}}
                ],
                "value": "--demo",
            }
        ]
    )

    _, game_args = ArgumentBuilder.build(version=version, context={}, settings=make_settings(), account=make_account())

    assert "--demo" not in game_args


def test_build_accepts_rule_based_entry_when_context_enables_feature():
    version = make_version(
        game_arguments=[
            {
                "rules": [
                    {"action": "allow", "features": {"is_demo_user": True}}
                ],
                "value": "--demo",
            }
        ]
    )

    _, game_args = ArgumentBuilder.build(version=version, context={"argument_features": {"is_demo_user": True}}, settings=make_settings(), account=make_account())

    assert "--demo" in game_args


def test_build_respects_last_matching_argument_rule():
    version = make_version(
        jvm_arguments=[
            {
                "rules": [
                    {"action": "allow"},
                    {"action": "disallow"},
                ],
                "value": "-Dblocked=true",
            }
        ]
    )

    jvm_args, _ = ArgumentBuilder.build(version=version, context={}, settings=make_settings(), account=make_account())

    assert "-Dblocked=true" not in jvm_args
