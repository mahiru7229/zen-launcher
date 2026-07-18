from pathlib import Path
import json
import zipfile

import pytest

from src.core.instance.errors import InstanceModChangeBlockedError
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.mod.mod_manager import ModManager
from src.models.instance.instance import Instance


def make_instance(tmp_path: Path, loader=("fabric", "0.19.3")) -> Instance:
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    return Instance(instance_id="instance-id", name="Test", version_id="1.20.1", instance_dir=instance_dir, mod_loader=loader)


def make_mod(path: Path, mod_id="example", name="Example Mod", version="1.0.0") -> Path:
    metadata = {
        "schemaVersion": 1,
        "id": mod_id,
        "name": name,
        "version": version,
        "description": "A test Fabric mod.",
        "environment": "client",
        "authors": ["Mahiru"],
        "license": "MIT",
        "depends": {"fabricloader": ">=0.15.0", "minecraft": "1.20.1"},
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("fabric.mod.json", json.dumps(metadata))
    return path


@pytest.fixture(autouse=True)
def unlocked(monkeypatch):
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda instance: False)


def test_add_scan_disable_enable_and_remove_mod(tmp_path):
    instance = make_instance(tmp_path)
    source = make_mod(tmp_path / "example.jar")

    added = ModManager.add_mods(instance, [source])
    scanned = ModManager.list_mods(instance)

    assert added[0].mod_id == "example"
    assert scanned[0].enabled is True
    assert scanned[0].dependencies["minecraft"] == "1.20.1"

    disabled = ModManager.set_enabled(instance, [scanned[0].path], False)
    assert disabled[0].enabled is False
    assert disabled[0].path.name.endswith(".jar.disabled")

    enabled = ModManager.set_enabled(instance, [disabled[0].path], True)
    assert enabled[0].enabled is True

    ModManager.remove_mods(instance, [enabled[0].path])
    assert ModManager.list_mods(instance) == []


def test_rejects_non_fabric_jar(tmp_path):
    instance = make_instance(tmp_path)
    source = tmp_path / "other.jar"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0")

    with pytest.raises(RuntimeError, match="fabric.mod.json"):
        ModManager.add_mods(instance, [source])


def test_rejects_mod_changes_for_vanilla_instance(tmp_path):
    instance = make_instance(tmp_path, loader=("vanilla", "-1"))
    source = make_mod(tmp_path / "example.jar")

    with pytest.raises(RuntimeError, match="does not use Fabric"):
        ModManager.add_mods(instance, [source])


def test_blocks_mod_changes_while_instance_is_running(tmp_path, monkeypatch):
    instance = make_instance(tmp_path)
    source = make_mod(tmp_path / "example.jar")
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda current: True)

    with pytest.raises(InstanceModChangeBlockedError):
        ModManager.add_mods(instance, [source])


def test_replace_same_mod_file_does_not_delete_source(tmp_path):
    instance = make_instance(tmp_path)
    source = make_mod(tmp_path / "example.jar")
    installed = ModManager.add_mods(instance, [source])[0]

    replaced = ModManager.add_mods(instance, [installed.path], replace=True)

    assert installed.path.exists()
    assert replaced[0].mod_id == "example"


def make_forge_mod(path: Path, mod_id="forge_example", name="Forge Example", version="1.0.0") -> Path:
    metadata = (
        'modLoader="javafml"\n'
        'loaderVersion="[47,)"\n'
        'license="MIT"\n\n'
        '[[mods]]\n'
        f'modId="{mod_id}"\n'
        f'version="{version}"\n'
        f'displayName="{name}"\n'
        'authors="Mahiru"\n'
        'description="A Forge test mod."\n'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/mods.toml", metadata)
    return path


def test_adds_and_reads_forge_mod(tmp_path):
    instance = make_instance(tmp_path, loader=("forge", "47.3.0"))
    source = make_forge_mod(tmp_path / "forge-example.jar")

    added = ModManager.add_mods(instance, [source])

    assert added[0].mod_id == "forge_example"
    assert added[0].name == "Forge Example"
    assert added[0].version == "1.0.0"
    assert added[0].status == "Ready"
