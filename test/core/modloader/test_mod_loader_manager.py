from types import SimpleNamespace

from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.fabric.fabric_version_manager import FabricVersionManager
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
