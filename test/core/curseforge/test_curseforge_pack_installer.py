from pathlib import PurePosixPath

import pytest

from src.core.curseforge.curseforge_pack_installer import CurseForgePackInstaller


def test_parses_primary_forge_loader() -> None:
    manifest = {
        "minecraft": {
            "version": "1.20.1",
            "modLoaders": [
                {"id": "forge-47.3.0", "primary": True},
                {"id": "forge-47.2.0", "primary": False},
            ],
        }
    }

    assert CurseForgePackInstaller._parse_loader(manifest) == ("1.20.1", "47.3.0")


def test_rejects_non_forge_pack() -> None:
    manifest = {"minecraft": {"version": "1.20.1", "modLoaders": [{"id": "fabric-0.16.0", "primary": True}]}}

    with pytest.raises(RuntimeError, match="Only Forge CurseForge modpacks"):
        CurseForgePackInstaller._parse_loader(manifest)


@pytest.mark.parametrize("value", ["../outside", "/absolute", "C:/windows", "folder/../../escape", ""])
def test_rejects_unsafe_override_paths(value: str) -> None:
    with pytest.raises(RuntimeError, match="Unsafe"):
        CurseForgePackInstaller._safe_relative_path(value)


def test_accepts_safe_override_path() -> None:
    assert CurseForgePackInstaller._safe_relative_path("config/example.toml") == PurePosixPath("config/example.toml")
