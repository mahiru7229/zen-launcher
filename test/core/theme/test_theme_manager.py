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


def write_manifest(root: Path, assets: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "theme.json").write_text(json.dumps({"schema_version": 1, "id": root.name, "name": "Test Theme", "author": "Test", "assets": assets}), encoding="utf-8")


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


def test_repository_default_manifest_matches_theme_catalog() -> None:
    from src.core.theme.theme_catalog import THEME_ASSET_BY_KEY

    project_root = Path(__file__).resolve().parents[3]
    payload = json.loads((project_root / "themes" / "mcw-default" / "theme.json").read_text(encoding="utf-8"))

    assert set(payload["assets"]) == set(THEME_ASSET_BY_KEY)
    assert "button.launch" in payload["assets"]
    assert "button.launch_disabled" in payload["assets"]


def test_legacy_theme_manifest_exposes_existing_png_assets() -> None:
    project_root = Path(__file__).resolve().parents[3]
    manager = ThemeManager(project_root / "themes")
    selected = manager.select("mcw-legacy-assets")

    assert selected.theme_id == "mcw-legacy-assets"
    assert manager.resolve_asset("logo.main", selected) is not None
    assert manager.resolve_asset("logo.sidebar", selected) is not None
    assert manager.resolve_asset("button.launch", selected) is not None
