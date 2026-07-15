from pathlib import Path
import json
import zipfile

from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.mod.mod_compatibility_manager import ModCompatibilityManager
from src.models.instance.instance import Instance


def make_instance(tmp_path: Path) -> Instance:
    instance_dir = tmp_path / "instance"
    (instance_dir / "mods").mkdir(parents=True)
    return Instance(instance_id="id", name="Test", version_id="1.20.1", instance_dir=instance_dir, mod_loader=("fabric", "0.16.0"))


def write_mod(path: Path, mod_id: str, version: str = "1.0.0", depends=None, conflicts=None, breaks=None, enabled=True) -> Path:
    metadata = {"schemaVersion": 1, "id": mod_id, "name": mod_id, "version": version, "environment": "client", "depends": depends or {}}
    if conflicts:
        metadata["conflicts"] = conflicts
    if breaks:
        metadata["breaks"] = breaks
    target = path if enabled else path.with_name(path.name + ".disabled")
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("fabric.mod.json", json.dumps(metadata))
    return target


def test_detects_duplicate_and_missing_fabric_api(tmp_path, monkeypatch):
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda instance: False)
    instance = make_instance(tmp_path)
    mods = instance.instance_dir / "mods"
    write_mod(mods / "first.jar", "example", depends={"fabric-api": ">=0.90.0"})
    write_mod(mods / "second.jar", "example")

    report = ModCompatibilityManager.scan(instance)

    codes = {issue.code for issue in report.issues}
    assert "duplicate-mod-id" in codes
    assert "dependency-missing" in codes
    assert report.error_count == 2


def test_detects_disabled_and_wrong_dependency_version(tmp_path, monkeypatch):
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda instance: False)
    instance = make_instance(tmp_path)
    mods = instance.instance_dir / "mods"
    write_mod(mods / "library.jar", "library", version="1.0.0", enabled=False)
    write_mod(mods / "consumer.jar", "consumer", depends={"library": ">=2.0.0"})

    report = ModCompatibilityManager.scan(instance)

    assert any(issue.code == "dependency-disabled" for issue in report.issues)


def test_detects_breaks_declaration(tmp_path, monkeypatch):
    monkeypatch.setattr(InstanceRunLock, "is_active", lambda instance: False)
    instance = make_instance(tmp_path)
    mods = instance.instance_dir / "mods"
    write_mod(mods / "a.jar", "a", breaks={"b": "*"})
    write_mod(mods / "b.jar", "b")

    report = ModCompatibilityManager.scan(instance)

    assert any(issue.code == "breaks" and issue.severity == "error" for issue in report.issues)
