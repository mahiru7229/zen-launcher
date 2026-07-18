from pathlib import Path

from src.core.fs.paths import Paths
from src.core.modloader.forge.forge_version_manager import ForgeVersionManager
from src.models.minecraft.version import Version


def make_version(tmp_path: Path) -> Version:
    raw = {
        "id": "1.20.1",
        "arguments": {"game": ["--demo"], "jvm": ["-Dbase=true"]},
        "libraries": [{"name": "com.example:base:1.0"}],
        "downloads": {"client": {"url": "https://example/client.jar", "sha1": "a" * 40, "size": 1}},
        "assetIndex": {"id": "1.20", "url": "https://example/assets.json", "sha1": "b" * 40, "size": 1},
        "assets": "1.20",
        "mainClass": "net.minecraft.client.main.Main",
        "javaVersion": {"majorVersion": 17},
    }
    return Version(
        id="1.20.1",
        arguments=raw["arguments"],
        minecraft_arguments=None,
        libraries=raw["libraries"],
        downloads=raw["downloads"],
        asset_index=raw["assetIndex"],
        assets=raw["assets"],
        main_class=raw["mainClass"],
        java_version=raw["javaVersion"],
        raw_json=raw,
        path=tmp_path / "1.20.1.json",
        type="release",
    )


def test_merge_profiles_keeps_base_and_adds_forge() -> None:
    base = make_version(Path(".")).raw_json
    profile = {
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",
        "arguments": {"game": ["--fml.forgeVersion", "47.3.0"], "jvm": ["-Dforge=true"]},
        "libraries": [{"name": "net.minecraftforge:forge:1.20.1-47.3.0"}],
    }

    merged = ForgeVersionManager._merge_profiles(base, profile, "1.20.1", "47.3.0")

    assert merged["mainClass"] == profile["mainClass"]
    assert merged["inheritsFrom"] == "1.20.1"
    assert len(merged["libraries"]) == 2
    assert merged["arguments"]["game"][-2:] == ["--fml.forgeVersion", "47.3.0"]
    assert merged["forge"]["loaderVersion"] == "47.3.0"


def test_prepare_staging_writes_launcher_layout(monkeypatch, tmp_path: Path) -> None:
    version = make_version(tmp_path)
    cached_client = tmp_path / "cache" / "1.20.1.jar"
    cached_client.parent.mkdir()
    cached_client.write_bytes(b"client")
    monkeypatch.setattr(Paths, "client", staticmethod(lambda current: cached_client))

    staging = tmp_path / "staging"
    staging.mkdir()
    ForgeVersionManager._prepare_staging(version, staging)

    assert (staging / "launcher_profiles.json").is_file()
    assert (staging / "versions" / "1.20.1" / "1.20.1.json").is_file()
    assert (staging / "versions" / "1.20.1" / "1.20.1.jar").read_bytes() == b"client"
