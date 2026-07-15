from __future__ import annotations

import json
from pathlib import Path
import struct
import zlib

from src.core.theme.theme_manager import ThemeManager


def write_png(path: Path, width: int = 4, height: int = 4) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    rows = b"".join(b"\x00" + (b"\x00\x00\x00\x00" * width) for _ in range(height))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    path.write_bytes(signature + chunk(b"IHDR", ihdr_data) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def write_manifest(root: Path, assets: dict[str, str], text_assets: dict[str, str] | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "id": root.name, "name": "Test Theme", "author": "Test", "assets": assets}
    if text_assets is not None:
        payload["text_assets"] = text_assets
    (root / "theme.json").write_text(json.dumps(payload), encoding="utf-8")


def test_valid_png_asset_is_resolved(tmp_path: Path) -> None:
    theme_root = tmp_path / "themes" / "test-theme"
    write_manifest(theme_root, {"background.window": "backgrounds/window.png"})
    write_png(theme_root / "backgrounds" / "window.png", 1600, 900)

    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("test-theme")

    assert selected.theme_id == "test-theme"
    assert manager.resolve_asset("background.window") == (theme_root / "backgrounds" / "window.png").resolve()


def test_missing_or_invalid_png_falls_back_without_crashing(tmp_path: Path) -> None:
    theme_root = tmp_path / "themes" / "test-theme"
    write_manifest(theme_root, {"background.window": "backgrounds/missing.png", "logo.main": "logos/broken.png"})
    broken = theme_root / "logos" / "broken.png"
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_text("not a png", encoding="utf-8")

    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("test-theme")

    assert selected.theme_id == "test-theme"
    assert selected.issues
    assert manager.resolve_asset("background.window") is None
    assert manager.resolve_asset("logo.main") is None


def test_unsafe_theme_asset_path_is_ignored(tmp_path: Path) -> None:
    theme_root = tmp_path / "themes" / "test-theme"
    write_manifest(theme_root, {"background.window": "../outside.png"})

    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("test-theme")

    assert selected.theme_id == "test-theme"
    assert "background.window" not in selected.assets
    assert manager.resolve_asset("background.window") is None


def test_invalid_theme_manifest_does_not_break_catalog(tmp_path: Path) -> None:
    invalid = tmp_path / "themes" / "invalid"
    invalid.mkdir(parents=True)
    (invalid / "theme.json").write_text("{broken", encoding="utf-8")

    manager = ThemeManager(tmp_path / "themes")

    assert [theme.theme_id for theme in manager.available_themes()] == [ThemeManager.FALLBACK_THEME_ID]
    assert manager.select("missing").theme_id == ThemeManager.FALLBACK_THEME_ID


def test_static_text_role_resolves_only_when_mapped_png_is_valid(tmp_path: Path) -> None:
    theme_root = tmp_path / "themes" / "test-theme"
    write_manifest(theme_root, {"button.launch": "controls/launch.png"}, {"control.launch": "button.launch"})
    write_png(theme_root / "controls" / "launch.png", 461, 133)

    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("test-theme")

    assert selected.text_assets == {"control.launch": "button.launch"}
    assert manager.resolve_text_asset("control.launch") == (theme_root / "controls" / "launch.png").resolve()


def test_static_text_role_falls_back_when_png_is_missing(tmp_path: Path) -> None:
    theme_root = tmp_path / "themes" / "test-theme"
    write_manifest(theme_root, {"button.launch": "controls/missing.png"}, {"control.launch": "button.launch"})

    manager = ThemeManager(tmp_path / "themes")
    manager.select("test-theme")

    assert manager.resolve_text_asset("control.launch") is None


def test_unknown_static_text_asset_key_is_ignored(tmp_path: Path) -> None:
    theme_root = tmp_path / "themes" / "test-theme"
    write_manifest(theme_root, {}, {"control.launch": "button.unknown"})

    manager = ThemeManager(tmp_path / "themes")
    selected = manager.select("test-theme")

    assert selected.text_assets == {}
    assert any("Unknown text asset key" in issue for issue in selected.issues)


def test_cancel_artwork_falls_back_to_default_theme(tmp_path: Path) -> None:
    default_root = tmp_path / "themes" / ThemeManager.DEFAULT_THEME_ID
    write_manifest(default_root, {"button.cancel": "controls/cancel.png"}, {"control.cancel": "button.cancel"})
    write_png(default_root / "controls" / "cancel.png", 461, 133)

    custom_root = tmp_path / "themes" / "custom"
    write_manifest(custom_root, {"button.launch": "controls/launch.png"}, {"control.launch": "button.launch"})
    write_png(custom_root / "controls" / "launch.png", 461, 133)

    manager = ThemeManager(tmp_path / "themes")
    manager.select("custom")

    assert manager.resolve_asset("button.cancel") is None
    assert manager.resolve_asset("button.cancel", fallback_to_default=True) == (default_root / "controls" / "cancel.png").resolve()
    assert manager.resolve_text_asset("control.cancel", fallback_to_default=True) == (default_root / "controls" / "cancel.png").resolve()
