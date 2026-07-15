from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import struct
from threading import RLock
from typing import Any

from src.core.fs.paths import Paths
from src.core.theme.theme_catalog import THEME_ASSET_BY_KEY


class ThemeError(RuntimeError):
    pass


class ThemeManifestError(ThemeError):
    pass


class ThemeAssetError(ThemeError):
    pass


@dataclass(frozen=True)
class ThemeDefinition:
    theme_id: str
    name: str
    author: str
    root: Path | None
    assets: dict[str, str] = field(default_factory=dict)
    text_assets: dict[str, str] = field(default_factory=dict)
    issues: tuple[str, ...] = ()
    builtin_fallback: bool = False


class ThemeManager:
    DEFAULT_THEME_ID = "mcw-default"
    FALLBACK_THEME_ID = "builtin-css"
    MANIFEST_NAME = "theme.json"
    MAX_MANIFEST_BYTES = 512 * 1024

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else Paths.THEME_ROOT
        self._lock = RLock()
        self._themes: dict[str, ThemeDefinition] = {}
        self._current = self._fallback_theme()
        self.reload()

    @property
    def current(self) -> ThemeDefinition:
        with self._lock:
            return self._current

    def reload(self) -> tuple[ThemeDefinition, ...]:
        with self._lock:
            themes = {self.FALLBACK_THEME_ID: self._fallback_theme()}
            try:
                self.root.mkdir(parents=True, exist_ok=True)
                directories = sorted((path for path in self.root.iterdir() if path.is_dir()), key=lambda path: path.name.casefold())
            except OSError:
                directories = []

            for directory in directories:
                try:
                    definition = self._load_theme(directory)
                except ThemeError:
                    continue
                themes[definition.theme_id] = definition

            current_id = self._current.theme_id if self._current else self.DEFAULT_THEME_ID
            self._themes = themes
            self._current = themes.get(current_id) or themes.get(self.DEFAULT_THEME_ID) or themes[self.FALLBACK_THEME_ID]
            return self.available_themes()

    def available_themes(self) -> tuple[ThemeDefinition, ...]:
        with self._lock:
            return tuple(sorted(self._themes.values(), key=lambda theme: (theme.builtin_fallback, theme.name.casefold())))

    def select(self, theme_id: str) -> ThemeDefinition:
        normalized = str(theme_id or "").strip()
        with self._lock:
            self._current = self._themes.get(normalized) or self._themes.get(self.DEFAULT_THEME_ID) or self._themes[self.FALLBACK_THEME_ID]
            return self._current

    def resolve_asset(self, key: str, theme: ThemeDefinition | None = None, fallback_to_default: bool = False) -> Path | None:
        selected = theme or self.current
        resolved = self._resolve_asset_for_theme(str(key), selected)
        if resolved is not None or not fallback_to_default or selected.theme_id == self.DEFAULT_THEME_ID:
            return resolved
        with self._lock:
            fallback = self._themes.get(self.DEFAULT_THEME_ID)
        if fallback is None:
            return None
        return self._resolve_asset_for_theme(str(key), fallback)

    def resolve_text_asset(self, role: str, theme: ThemeDefinition | None = None, fallback_to_default: bool = False) -> Path | None:
        selected = theme or self.current
        asset_key = selected.text_assets.get(str(role))
        if asset_key:
            resolved = self.resolve_asset(asset_key, selected)
            if resolved is not None:
                return resolved
        if not fallback_to_default or selected.theme_id == self.DEFAULT_THEME_ID:
            return None
        with self._lock:
            fallback = self._themes.get(self.DEFAULT_THEME_ID)
        if fallback is None:
            return None
        fallback_key = fallback.text_assets.get(str(role))
        if not fallback_key:
            return None
        return self.resolve_asset(fallback_key, fallback)

    def _resolve_asset_for_theme(self, key: str, selected: ThemeDefinition) -> Path | None:
        if selected.root is None:
            return None
        relative = selected.assets.get(str(key))
        if not relative:
            return None
        try:
            candidate = self._safe_asset_path(selected.root, relative)
            self._validate_png(candidate)
            return candidate
        except ThemeAssetError:
            return None

    def asset_status(self, theme: ThemeDefinition | None = None) -> dict[str, bool]:
        selected = theme or self.current
        return {key: self.resolve_asset(key, selected) is not None for key in THEME_ASSET_BY_KEY}

    def _load_theme(self, directory: Path) -> ThemeDefinition:
        manifest_path = directory / self.MANIFEST_NAME
        if not manifest_path.is_file():
            raise ThemeManifestError(f"Missing {self.MANIFEST_NAME}: {directory}")
        try:
            if manifest_path.stat().st_size > self.MAX_MANIFEST_BYTES:
                raise ThemeManifestError(f"Theme manifest is too large: {manifest_path}")
            payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ThemeManifestError(f"Unable to read theme manifest: {manifest_path}") from error
        if not isinstance(payload, dict):
            raise ThemeManifestError("Theme manifest root must be an object.")

        theme_id = str(payload.get("id") or directory.name).strip()
        if not theme_id or theme_id in {".", ".."} or any(character in theme_id for character in "/\\:"):
            raise ThemeManifestError("Theme ID is invalid.")
        name = str(payload.get("name") or theme_id).strip()
        author = str(payload.get("author") or "Unknown").strip()
        raw_assets = payload.get("assets", {})
        if not isinstance(raw_assets, dict):
            raise ThemeManifestError("Theme assets must be an object.")
        raw_text_assets = payload.get("text_assets", {})
        if not isinstance(raw_text_assets, dict):
            raise ThemeManifestError("Theme text_assets must be an object.")

        assets: dict[str, str] = {}
        text_assets: dict[str, str] = {}
        issues: list[str] = []
        for key, value in raw_assets.items():
            normalized_key = str(key).strip()
            relative = str(value).strip()
            if normalized_key not in THEME_ASSET_BY_KEY:
                issues.append(f"Unknown asset key: {normalized_key}")
                continue
            try:
                candidate = self._safe_asset_path(directory, relative)
            except ThemeAssetError as error:
                issues.append(str(error))
                continue
            assets[normalized_key] = candidate.relative_to(directory.resolve()).as_posix()
            if candidate.is_file():
                try:
                    self._validate_png(candidate)
                except ThemeAssetError as error:
                    issues.append(str(error))

        for role, asset_key in raw_text_assets.items():
            normalized_role = str(role).strip()
            normalized_asset_key = str(asset_key).strip()
            if not normalized_role or any(character in normalized_role for character in "/\\:"):
                issues.append(f"Invalid static text role: {normalized_role!r}")
                continue
            if normalized_asset_key not in THEME_ASSET_BY_KEY:
                issues.append(f"Unknown text asset key for {normalized_role}: {normalized_asset_key}")
                continue
            text_assets[normalized_role] = normalized_asset_key

        return ThemeDefinition(theme_id=theme_id, name=name, author=author, root=directory.resolve(), assets=assets, text_assets=text_assets, issues=tuple(issues))

    @staticmethod
    def _safe_asset_path(root: Path, relative: str) -> Path:
        value = str(relative).replace("\\", "/").strip()
        if not value or value.startswith("/") or ":" in value.split("/", 1)[0]:
            raise ThemeAssetError(f"Unsafe theme asset path: {relative!r}")
        root_resolved = root.resolve()
        candidate = (root_resolved / value).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as error:
            raise ThemeAssetError(f"Theme asset escapes its theme directory: {relative!r}") from error
        if candidate.suffix.lower() != ".png":
            raise ThemeAssetError(f"Theme asset must be a PNG: {relative!r}")
        return candidate

    @staticmethod
    def _validate_png(path: Path) -> tuple[int, int]:
        try:
            with path.open("rb") as file:
                header = file.read(24)
        except OSError as error:
            raise ThemeAssetError(f"Unable to read theme PNG: {path}") from error
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise ThemeAssetError(f"Invalid PNG theme asset: {path}")
        width, height = struct.unpack(">II", header[16:24])
        if width <= 0 or height <= 0 or width > 16384 or height > 16384:
            raise ThemeAssetError(f"Invalid PNG dimensions: {path}")
        return width, height

    @classmethod
    def _fallback_theme(cls) -> ThemeDefinition:
        return ThemeDefinition(theme_id=cls.FALLBACK_THEME_ID, name="Built-in CSS fallback", author="MCW Launcher", root=None, builtin_fallback=True)


theme_manager = ThemeManager()
