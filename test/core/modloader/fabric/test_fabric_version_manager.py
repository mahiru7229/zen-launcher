from pathlib import Path

from src.core.fs.paths import Paths
from src.core.modloader.fabric.fabric_meta_client import FabricMetaClient
from src.core.modloader.fabric.fabric_version_manager import FabricVersionManager
from src.models.minecraft.version import Version


def make_base_version(tmp_path: Path) -> Version:
    raw = {
        "id": "1.20.1",
        "type": "release",
        "arguments": {"jvm": ["-Dvanilla=true"], "game": ["--username", "${auth_player_name}"]},
        "assetIndex": {"id": "5", "url": "https://example/assets", "sha1": "a" * 40, "size": 1, "totalSize": 1},
        "assets": "5",
        "downloads": {"client": {"url": "https://example/client.jar", "sha1": "b" * 40, "size": 1}},
        "javaVersion": {"majorVersion": 17},
        "libraries": [{"name": "vanilla:library:1", "downloads": {"artifact": {"path": "vanilla/library/1/library-1.jar", "url": "https://example/library.jar", "sha1": "c" * 40, "size": 1}}}],
        "mainClass": "net.minecraft.client.main.Main",
    }
    path = tmp_path / "1.20.1.json"
    path.write_text("{}", encoding="utf-8")
    return Version(id="1.20.1", path=path, libraries=raw["libraries"], downloads=raw["downloads"], asset_index=raw["assetIndex"], assets="5", main_class=raw["mainClass"], java_version=raw["javaVersion"], raw_json=raw, type="release", arguments=raw["arguments"], minecraft_arguments=None)


def test_merges_fabric_profile_with_vanilla_metadata(tmp_path):
    base = make_base_version(tmp_path)
    fabric = {
        "id": "fabric-loader-0.19.3-1.20.1",
        "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient",
        "arguments": {"jvm": ["-Dfabric=true"], "game": []},
        "libraries": [{"name": "net.fabricmc:fabric-loader:0.19.3", "downloads": {"artifact": {"path": "net/fabricmc/fabric-loader/0.19.3/fabric-loader-0.19.3.jar", "url": "https://example/fabric.jar", "sha1": "d" * 40, "size": 1}}}],
    }

    merged = FabricVersionManager._merge_profiles(base.raw_json, fabric, "0.19.3")

    assert merged["inheritsFrom"] == "1.20.1"
    assert merged["mainClass"].endswith("KnotClient")
    assert merged["arguments"]["jvm"] == ["-Dvanilla=true", "-Dfabric=true"]
    assert len(merged["libraries"]) == 2
    assert merged["fabric"]["loaderVersion"] == "0.19.3"


def test_installs_and_reuses_cached_profile(tmp_path, monkeypatch):
    base = make_base_version(tmp_path)
    monkeypatch.setattr(Paths, "CACHE_ROOT", tmp_path / "cache")
    calls = []
    profile = {
        "id": "fabric-loader-0.19.3-1.20.1",
        "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient",
        "arguments": {"jvm": ["-Dfabric=true"], "game": []},
        "libraries": [{"name": "net.fabricmc:fabric-loader:0.19.3", "url": "https://maven.fabricmc.net/"}],
    }

    def get_profile(game_version, loader_version):
        calls.append((game_version, loader_version))
        return profile

    monkeypatch.setattr(FabricMetaClient, "get_profile", get_profile)
    monkeypatch.setattr(FabricVersionManager, "_load_artifact_metadata", lambda url: ("e" * 40, 123))

    first = FabricVersionManager.install(base, "0.19.3")
    second = FabricVersionManager.install(base, "0.19.3")

    assert first.id == "fabric-loader-0.19.3-1.20.1"
    assert second.id == first.id
    assert calls == [("1.20.1", "0.19.3")]
    assert Paths.client(first) == Paths.CACHE_ROOT / "versions" / "1.20.1" / "1.20.1.jar"


def test_fabric_library_replaces_same_maven_module_from_base_profile():
    base_library = {"name": "example:shared:1.0.0"}
    fabric_library = {"name": "example:shared:2.0.0"}

    merged = FabricVersionManager._merge_libraries([base_library], [fabric_library])

    assert merged == [fabric_library]


def test_library_key_keeps_classifiers_separate():
    regular = FabricVersionManager._library_key("example:shared:1.0.0")
    native = FabricVersionManager._library_key("example:shared:1.0.0:natives-windows")

    assert regular != native
