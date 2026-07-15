from pathlib import Path
import hashlib

from src.core.modrinth.modrinth_pack_registry import ModrinthPackRegistry
from src.models.instance.instance import Instance


def test_scans_missing_and_modified_managed_files(tmp_path):
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    instance = Instance(instance_id="id", name="Pack", version_id="1.20.1", instance_dir=instance_dir, mod_loader=("fabric", "0.16.0"))
    content = b"original"
    target = instance_dir / "config" / "pack.json"
    target.parent.mkdir()
    target.write_bytes(content)
    ModrinthPackRegistry.save(instance_dir, {"projectId": "pack", "versionId": "v1", "managedFiles": [{"path": "config/pack.json", "sha1": hashlib.sha1(content).hexdigest(), "size": len(content), "source": "overrides"}, {"path": "mods/missing.jar", "sha1": "abc", "source": "download"}]})
    target.write_bytes(b"changed")

    report = ModrinthPackRegistry.scan(instance)

    assert report.modified_count == 1
    assert report.missing_count == 1
