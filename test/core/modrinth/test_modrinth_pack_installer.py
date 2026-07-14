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


def make_pack(path: Path, file_content: bytes = b"fabric-mod") -> Path:
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
        "dependencies": {"minecraft": "1.20.1", "fabric-loader": "0.16.0"},
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

    def fake_file_download(urls, destination, sha1="", sha512="", expected_size=0, force=False, restrict_hosts=True, max_retry=2):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fabric-mod")
        return destination

    monkeypatch.setattr(ModrinthDownloader, "download_urls", fake_file_download)
    monkeypatch.setattr(VersionManager, "load", lambda version_id: SimpleNamespace(id=version_id))
    monkeypatch.setattr(ModLoaderManager, "resolve", lambda game_version, loader_name, loader_version="auto": ("fabric", loader_version))
    monkeypatch.setattr(ModLoaderManager, "prepare", lambda version, loader_name, loader_version, reporter=None: version)

    result = ModrinthPackInstaller.install("pack-project", "pack-version", "Test Instance", True)

    instance_dir = tmp_path / "instances" / "Test Instance"
    assert result.instance.name == "Test Instance"
    assert (instance_dir / "mods" / "example.jar").read_bytes() == b"fabric-mod"
    assert (instance_dir / "config" / "example.json").is_file()
    assert (instance_dir / "options.txt").read_text(encoding="utf-8") == "fov:0.5"
    assert (instance_dir / ".mcw" / "modrinth-pack.json").is_file()


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
