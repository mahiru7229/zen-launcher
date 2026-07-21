from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import zipfile

import pytest

from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager
from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.modrinth.modrinth_downloader import ModrinthDownloader
from src.core.modrinth.modrinth_pack_installer import ModrinthPackInstaller
from src.models.modrinth.project import ModrinthProject
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def make_pack(path: Path, file_content: bytes = b"fabric-mod", loader: str = "fabric", loader_version: str = "0.16.0") -> Path:
    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": "pack-version",
        "name": "Test Pack",
        "summary": "Test",
        "files": [{
            "path": "mods/example.jar",
            "hashes": {"sha1": hashlib.sha1(file_content).hexdigest(), "sha512": hashlib.sha512(file_content).hexdigest()},
            "env": {"client": "required", "server": "optional"},
            "downloads": ["https://cdn.modrinth.com/data/project/example.jar"],
            "fileSize": len(file_content),
        }],
        "dependencies": {"minecraft": "1.20.1", "fabric-loader" if loader == "fabric" else "forge": loader_version},
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("modrinth.index.json", json.dumps(index))
        archive.writestr("overrides/config/example.json", "{}")
        archive.writestr("client-overrides/options.txt", "fov:0.5")
    return path


def configure_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(Paths, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(Paths, "INSTANCES_ROOT", tmp_path / "instances")
    monkeypatch.setattr(Paths, "INSTANCE_LOCKS_ROOT", tmp_path / "instances" / ".runtime" / "locks")


def test_rejects_unsafe_pack_paths():
    for value in ("../evil.jar", "/absolute.jar", "C:/evil.jar", "instance.json"):
        with pytest.raises(RuntimeError):
            ModrinthPackInstaller._safe_relative_path(value)


def test_installs_fabric_modpack_as_new_instance(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    pack_source = make_pack(tmp_path / "pack.mrpack")
    project = ModrinthProject(project_id="pack-project", slug="pack", title="Test Pack", description="", project_type="modpack")
    version = ModrinthVersion(version_id="pack-version", project_id="pack-project", name="1.0", version_number="1.0", version_type="release", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url="https://cdn.modrinth.com/pack.mrpack", filename="pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: project)
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: version)
    monkeypatch.setattr(ModrinthDownloader, "download_file", lambda file, destination, force=False: destination.parent.mkdir(parents=True, exist_ok=True) or destination.write_bytes(pack_source.read_bytes()) or destination)

    monkeypatch.setattr(VersionManager, "load", lambda version_id: SimpleNamespace(id=version_id))
    monkeypatch.setattr(ModLoaderManager, "resolve", lambda game_version, loader_name, loader_version="auto": ("fabric", loader_version))
    monkeypatch.setattr(ModLoaderManager, "prepare", lambda version, loader_name, loader_version, reporter=None: version)

    result = ModrinthPackInstaller.install("pack-project", "pack-version", "Test Instance", True)

    instance_dir = tmp_path / "instances" / "Test Instance"
    assert result.instance.name == "Test Instance"
    assert result.installed_files == 1
    assert not (instance_dir / "mods" / "example.jar").exists()
    assert (instance_dir / "config" / "example.json").is_file()
    assert (instance_dir / "options.txt").read_text(encoding="utf-8") == "fov:0.5"
    metadata_path = instance_dir / ".mcw" / "modrinth-pack.json"
    assert metadata_path.is_file()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["schemaVersion"] == 3
    assert {item["path"] for item in metadata["managedFiles"]} == {"mods/example.jar", "config/example.json", "options.txt"}
    queued = next(item for item in metadata["managedFiles"] if item["path"] == "mods/example.jar")
    assert queued["downloads"] == ["https://cdn.modrinth.com/data/project/example.jar"]


def test_cleanup_removes_instance_when_finalization_fails(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    pack_source = make_pack(tmp_path / "pack.mrpack")
    project = ModrinthProject(project_id="pack-project", slug="pack", title="Test Pack", description="", project_type="modpack")
    version = ModrinthVersion(version_id="pack-version", project_id="pack-project", name="1.0", version_number="1.0", version_type="release", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url="https://cdn.modrinth.com/pack.mrpack", filename="pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: project)
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: version)
    monkeypatch.setattr(ModrinthDownloader, "download_file", lambda file, destination, force=False: destination.parent.mkdir(parents=True, exist_ok=True) or destination.write_bytes(pack_source.read_bytes()) or destination)
    monkeypatch.setattr(ModrinthDownloader, "download_urls", lambda urls, destination, **kwargs: destination.parent.mkdir(parents=True, exist_ok=True) or destination.write_bytes(b"fabric-mod") or destination)
    monkeypatch.setattr(VersionManager, "load", lambda version_id: SimpleNamespace(id=version_id))
    monkeypatch.setattr(ModLoaderManager, "resolve", lambda game_version, loader_name, loader_version="auto": ("fabric", loader_version))
    monkeypatch.setattr(ModLoaderManager, "prepare", lambda version, loader_name, loader_version, reporter=None: version)
    monkeypatch.setattr(ModrinthPackInstaller, "_write_metadata", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("finalization failed")))

    with pytest.raises(RuntimeError, match="finalization failed"):
        ModrinthPackInstaller.install("pack-project", "pack-version", "Broken Instance", True)

    assert not InstanceManager.is_instance_exist("Broken Instance")
    assert not (tmp_path / "instances" / "Broken Instance").exists()



def test_blank_modpack_name_uses_next_available_project_name(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    (tmp_path / "instances" / "Test Pack").mkdir(parents=True)
    (tmp_path / "instances" / "Test Pack (2)").mkdir(parents=True)

    assert InstanceManager.next_available_name("Test Pack") == "Test Pack (3)"


def test_modpack_version_respects_enabled_release_channels(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    project = ModrinthProject(project_id="pack-project", slug="pack", title="Test Pack", description="", project_type="modpack")
    version = ModrinthVersion(version_id="pack-alpha", project_id="pack-project", name="Alpha", version_number="1.0-alpha", version_type="alpha", game_versions=("1.20.1",), loaders=("fabric",), files=(ModrinthFile(url="https://cdn.modrinth.com/pack.mrpack", filename="pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: project)
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: version)

    with pytest.raises(RuntimeError, match="disabled alpha channel"):
        ModrinthPackInstaller.install("pack-project", "pack-alpha", "Alpha Pack", True, ("release",))


def test_installs_forge_modpack_with_declared_forge_version(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    pack_source = make_pack(tmp_path / "forge-pack.mrpack", file_content=b"forge-mod", loader="forge", loader_version="47.4.21")
    project = ModrinthProject(project_id="forge-pack", slug="forge-pack", title="Forge Pack", description="", project_type="modpack")
    version = ModrinthVersion(version_id="forge-version", project_id="forge-pack", name="1.0", version_number="1.0", version_type="release", game_versions=("1.20.1",), loaders=("forge",), files=(ModrinthFile(url="https://cdn.modrinth.com/forge-pack.mrpack", filename="forge-pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))
    calls = []
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: project)
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: version)
    monkeypatch.setattr(ModrinthDownloader, "download_file", lambda file, destination, force=False: destination.parent.mkdir(parents=True, exist_ok=True) or destination.write_bytes(pack_source.read_bytes()) or destination)
    base_version = SimpleNamespace(id="1.20.1")
    monkeypatch.setattr(VersionManager, "load", lambda version_id: base_version)
    monkeypatch.setattr(ModLoaderManager, "resolve", lambda game_version, loader_name, loader_version="auto": calls.append(("resolve", game_version, loader_name, loader_version)) or (loader_name, loader_version))
    monkeypatch.setattr(ModLoaderManager, "prepare", lambda version, loader_name, loader_version, reporter=None: calls.append(("prepare", loader_name, loader_version)) or version)

    result = ModrinthPackInstaller.install("forge-pack", "forge-version", "Forge Instance", True, expected_loader="forge")

    assert result.instance.mod_loader == ("forge", "47.4.21")
    assert ("resolve", "1.20.1", "forge", "47.4.21") in calls
    assert ("prepare", "forge", "47.4.21") in calls
    metadata = json.loads((tmp_path / "instances" / "Forge Instance" / ".mcw" / "modrinth-pack.json").read_text(encoding="utf-8"))
    assert metadata["loader"] == "forge"
    assert metadata["loaderVersion"] == "47.4.21"


def test_rejects_modpack_when_browser_loader_filter_does_not_match_manifest(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    pack_source = make_pack(tmp_path / "forge-pack.mrpack", loader="forge", loader_version="47.4.21")
    project = ModrinthProject(project_id="forge-pack", slug="forge-pack", title="Forge Pack", description="", project_type="modpack")
    version = ModrinthVersion(version_id="forge-version", project_id="forge-pack", name="1.0", version_number="1.0", version_type="release", game_versions=("1.20.1",), loaders=("forge",), files=(ModrinthFile(url="https://cdn.modrinth.com/forge-pack.mrpack", filename="forge-pack.mrpack", sha1="a", sha512="b", size=1, primary=True),))
    monkeypatch.setattr(ModrinthClient, "get_project", lambda project_id: project)
    monkeypatch.setattr(ModrinthClient, "get_version", lambda version_id: version)
    monkeypatch.setattr(ModrinthDownloader, "download_file", lambda file, destination, force=False: destination.parent.mkdir(parents=True, exist_ok=True) or destination.write_bytes(pack_source.read_bytes()) or destination)

    with pytest.raises(RuntimeError, match="browser filter is set to Fabric"):
        ModrinthPackInstaller.install("forge-pack", "forge-version", "Wrong Filter", True, expected_loader="fabric")


def test_parse_dependencies_rejects_neoforge_and_ambiguous_loaders():
    with pytest.raises(RuntimeError, match="unsupported loader"):
        ModrinthPackInstaller._parse_dependencies({"dependencies": {"minecraft": "1.20.1", "neoforge": "20.1.1"}})
    with pytest.raises(RuntimeError, match="more than one"):
        ModrinthPackInstaller._parse_dependencies({"dependencies": {"minecraft": "1.20.1", "fabric-loader": "0.16.0", "forge": "47.4.21"}})
