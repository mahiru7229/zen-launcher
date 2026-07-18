from types import SimpleNamespace

from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.fabric.fabric_version_manager import FabricVersionManager
from src.core.modloader.forge.forge_version_manager import ForgeVersionManager
from src.core.modloader.mod_loader_manager import ModLoaderManager


def test_loads_vanilla_version(monkeypatch):
    expected = object()
    monkeypatch.setattr(VersionManager, "load", lambda version_id: expected)
    instance = SimpleNamespace(version_id="1.20.1", mod_loader=("vanilla", "-1"))

    assert ModLoaderManager.load(instance) is expected


def test_loads_fabric_version(monkeypatch):
    expected = object()
    monkeypatch.setattr(FabricVersionManager, "load", lambda game_version, loader_version, reporter=None: expected)
    instance = SimpleNamespace(version_id="1.20.1", mod_loader=("fabric", "0.19.3"))

    assert ModLoaderManager.load(instance) is expected


def test_resolve_fabric_auto_uses_recommended_loader(monkeypatch):
    monkeypatch.setattr(FabricVersionManager, "recommended_loader_version", lambda game_version: "0.19.3")

    assert ModLoaderManager.resolve("1.21.1", "fabric", "auto") == ("fabric", "0.19.3")


def test_resolve_fabric_keeps_explicit_loader_version(monkeypatch):
    def unexpected_call(game_version):
        raise AssertionError("Explicit loader versions must not query the recommended version.")

    monkeypatch.setattr(FabricVersionManager, "recommended_loader_version", unexpected_call)

    assert ModLoaderManager.resolve("1.21.1", "fabric", "0.18.6") == ("fabric", "0.18.6")


def test_resolve_vanilla_normalizes_version():
    assert ModLoaderManager.resolve("1.21.1", "vanilla", "auto") == ("vanilla", "-1")


def test_resolve_fabric_legacy_missing_version_uses_recommended_loader(monkeypatch):
    monkeypatch.setattr(FabricVersionManager, "recommended_loader_version", lambda game_version: "0.19.3")

    assert ModLoaderManager.resolve("1.21.1", "fabric", "-1") == ("fabric", "0.19.3")


def test_repairs_fabric_instance(monkeypatch):
    expected = object()
    instance = SimpleNamespace(version_id="1.20.1", mod_loader=("fabric", "0.19.3"))
    base_version = object()
    monkeypatch.setattr(VersionManager, "load", lambda version_id: base_version)
    monkeypatch.setattr(FabricVersionManager, "repair", lambda version, loader_version, reporter=None: expected)

    assert ModLoaderManager.repair(instance) is expected


def test_repair_rejects_vanilla_instance():
    instance = SimpleNamespace(version_id="1.20.1", mod_loader=("vanilla", "-1"))

    import pytest

    with pytest.raises(RuntimeError, match="Only Fabric instances"):
        ModLoaderManager.repair(instance)



def test_loads_forge_version(monkeypatch):
    expected = object()
    monkeypatch.setattr(ForgeVersionManager, "load", lambda game_version, loader_version, reporter=None: expected)
    instance = SimpleNamespace(version_id="1.20.1", mod_loader=("forge", "47.3.0"))

    assert ModLoaderManager.load(instance) is expected


def test_resolve_forge_auto_uses_recommended_loader(monkeypatch):
    monkeypatch.setattr(ForgeVersionManager, "recommended_loader_version", lambda game_version: "47.3.0")

    assert ModLoaderManager.resolve("1.20.1", "forge", "auto") == ("forge", "47.3.0")


def test_repairs_forge_instance(monkeypatch):
    expected = object()
    instance = SimpleNamespace(version_id="1.20.1", mod_loader=("forge", "47.3.0"))
    base_version = object()
    monkeypatch.setattr(VersionManager, "load", lambda version_id: base_version)
    monkeypatch.setattr(ForgeVersionManager, "repair", lambda version, loader_version, reporter=None: expected)

    assert ModLoaderManager.repair(instance) is expected
