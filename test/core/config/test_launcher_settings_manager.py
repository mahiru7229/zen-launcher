from __future__ import annotations

import json
from pathlib import Path

from src.core.config.launcher_settings_manager import LauncherSettingsManager


def test_initialize_creates_launcher_settings_file(tmp_path: Path) -> None:
    path = tmp_path / "config" / "launcher_settings.json"
    manager = LauncherSettingsManager(path)

    assert manager.initialize() == path
    assert path.exists()
    assert manager.load()["gui"]["language"] == "en-US"


def test_save_updates_sections_and_preserves_unknown_options(tmp_path: Path) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")
    manager.save({
        "gui": {"language": "vi-VN", "future_option": "kept"},
        "launch": {"debug_mode": True},
        "plugins": {"example": True},
    })

    manager.save({"gui": {"show_snapshots": True}})
    data = manager.load()

    assert data["gui"]["language"] == "vi-VN"
    assert data["gui"]["show_snapshots"] is True
    assert data["gui"]["future_option"] == "kept"
    assert data["launch"]["debug_mode"] is True
    assert data["plugins"] == {"example": True}


def test_invalid_file_is_backed_up_and_recreated(tmp_path: Path) -> None:
    path = tmp_path / "launcher_settings.json"
    path.write_text("not json", encoding="utf-8")
    manager = LauncherSettingsManager(path)

    data = manager.load()

    assert data["schema_version"] == manager.SCHEMA_VERSION
    assert json.loads(path.read_text(encoding="utf-8"))["gui"]["start_page"] == "home"
    assert (tmp_path / "launcher_settings.json.broken").read_text(encoding="utf-8") == "not json"


def test_window_geometry_round_trip(tmp_path: Path) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")
    geometry = b"\x00\x01window-geometry\xff"

    manager.save_window_geometry(geometry)

    assert manager.load_window_geometry() == geometry


def test_reset_restores_defaults(tmp_path: Path) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")
    manager.save({"gui": {"language": "vi-VN"}, "launch": {"debug_mode": True}})

    data = manager.reset()

    assert data == manager.DEFAULT_SETTINGS
    assert manager.load() == manager.DEFAULT_SETTINGS


def test_update_settings_are_created_and_persisted(tmp_path: Path) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")

    data = manager.load()
    assert data["updates"] == {
        "auto_check": True,
        "channel": "stable",
        "channel_policy_version": manager.UPDATE_CHANNEL_POLICY_VERSION,
        "last_checked_at": None,
    }

    manager.update_section("updates", {"auto_check": False, "last_checked_at": "2026-07-15T12:00:00+00:00"})
    updated = manager.load()["updates"]
    assert updated["auto_check"] is False
    assert updated["channel"] == "stable"
    assert updated["last_checked_at"] == "2026-07-15T12:00:00+00:00"


def test_existing_beta_channel_is_migrated_to_stable_once(tmp_path: Path) -> None:
    path = tmp_path / "launcher_settings.json"
    path.write_text(json.dumps({
        "schema_version": 5,
        "updates": {
            "auto_check": True,
            "channel": "beta",
            "last_checked_at": None,
        },
    }), encoding="utf-8")
    manager = LauncherSettingsManager(path)

    migrated = manager.load()["updates"]

    assert migrated["channel"] == "stable"
    assert migrated["channel_policy_version"] == manager.UPDATE_CHANNEL_POLICY_VERSION


def test_user_can_opt_back_into_beta_after_stable_migration(tmp_path: Path) -> None:
    path = tmp_path / "launcher_settings.json"
    path.write_text(json.dumps({
        "schema_version": 5,
        "updates": {"channel": "beta"},
    }), encoding="utf-8")
    manager = LauncherSettingsManager(path)

    assert manager.load()["updates"]["channel"] == "stable"
    manager.update_section("updates", {"channel": "beta"})

    assert manager.load()["updates"]["channel"] == "beta"


def test_already_migrated_beta_opt_in_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "launcher_settings.json"
    path.write_text(json.dumps({
        "schema_version": 6,
        "updates": {
            "auto_check": True,
            "channel": "beta",
            "channel_policy_version": LauncherSettingsManager.UPDATE_CHANNEL_POLICY_VERSION,
            "last_checked_at": None,
        },
    }), encoding="utf-8")
    manager = LauncherSettingsManager(path)

    assert manager.load()["updates"]["channel"] == "beta"


def test_theme_and_modrinth_channels_are_created_and_persisted(tmp_path: Path) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")

    data = manager.load()
    assert data["appearance"] == {"theme": "mcw-default", "show_static_text": True}
    assert data["modrinth"] == {"include_beta": False, "include_alpha": False}

    manager.save({"appearance": {"theme": "pixel-night", "show_static_text": "off"}, "modrinth": {"include_beta": True, "include_alpha": "yes"}})
    updated = manager.load()

    assert updated["appearance"] == {"theme": "pixel-night", "show_static_text": False}
    assert updated["modrinth"] == {"include_beta": True, "include_alpha": True}


def test_download_limit_is_unlimited_by_default_and_normalized(tmp_path: Path) -> None:
    manager = LauncherSettingsManager(tmp_path / "launcher_settings.json")

    assert manager.load()["network"] == {"download_limit_mbps": 0.0}

    manager.update_section("network", {"download_limit_mbps": "12.5"})
    assert manager.load()["network"]["download_limit_mbps"] == 12.5

    manager.update_section("network", {"download_limit_mbps": -1})
    assert manager.load()["network"]["download_limit_mbps"] == 0.0

    manager.update_section("network", {"download_limit_mbps": 5000})
    assert manager.load()["network"]["download_limit_mbps"] == 1024.0
