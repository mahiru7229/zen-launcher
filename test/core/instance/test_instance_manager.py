from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.fs.paths import Paths
from src.core.instance.instance_manager import InstanceManager


@pytest.fixture
def temporary_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Chuyển toàn bộ dữ liệu instance sang thư mục tạm.

    Nhờ đó test không làm thay đổi dữ liệu thật trong project.
    """
    instances_root = tmp_path / "instances"

    monkeypatch.setattr(
        Paths,
        "INSTANCES_ROOT",
        instances_root
    )

    return instances_root


@pytest.fixture
def fake_version():
    """
    InstanceManager.create() hiện chỉ cần thuộc tính version.id,
    nên không cần tạo Version thật.
    """
    return SimpleNamespace(id="1.20.1")


def test_create_instance_has_correct_instance_dir(
    temporary_paths: Path,
    fake_version
):
    instance = InstanceManager.create(
        name="Test Instance",
        version=fake_version
    )

    expected_dir = temporary_paths / "Test Instance"

    assert instance.name == "Test Instance"
    assert instance.version_id == "1.20.1"

    assert isinstance(instance.instance_dir, Path)
    assert instance.instance_dir == expected_dir

    assert expected_dir.exists()
    assert expected_dir.is_dir()

    assert (expected_dir / "instance.json").exists()


def test_load_instance_returns_path_instance_dir(
    temporary_paths: Path,
    fake_version
):
    InstanceManager.create(
        name="Load Test",
        version=fake_version
    )

    loaded_instance = InstanceManager.load("Load Test")

    expected_dir = temporary_paths / "Load Test"

    assert loaded_instance.name == "Load Test"

    assert isinstance(loaded_instance.instance_dir, Path)
    assert loaded_instance.instance_dir == expected_dir

    assert loaded_instance.instance_dir.exists()


def test_clone_updates_instance_directory(
    temporary_paths: Path,
    fake_version
):
    source_instance = InstanceManager.create(
        name="Source Instance",
        version=fake_version
    )

    test_file = source_instance.instance_dir / "test.txt"
    test_file.write_text(
        "MCW Launcher",
        encoding="utf-8"
    )

    cloned_instance = InstanceManager.clone(
        source_name="Source Instance",
        new_name="Cloned Instance"
    )

    expected_dir = temporary_paths / "Cloned Instance"

    assert cloned_instance.name == "Cloned Instance"

    assert isinstance(cloned_instance.instance_dir, Path)
    assert cloned_instance.instance_dir == expected_dir

    assert cloned_instance.instance_id != source_instance.instance_id

    assert expected_dir.exists()
    assert (expected_dir / "test.txt").exists()
    assert (expected_dir / "instance.json").exists()

    loaded_clone = InstanceManager.load("Cloned Instance")

    assert loaded_clone.instance_dir == expected_dir
    assert loaded_clone.name == "Cloned Instance"


def test_rename_updates_instance_directory(
    temporary_paths: Path,
    fake_version
):
    original_instance = InstanceManager.create(
        name="Old Name",
        version=fake_version
    )

    old_dir = original_instance.instance_dir
    new_dir = temporary_paths / "New Name"

    result = InstanceManager.rename(
        instance_name="Old Name",
        new_name="New Name"
    )

    assert result == new_dir

    assert not old_dir.exists()
    assert new_dir.exists()

    renamed_instance = InstanceManager.load("New Name")

    assert renamed_instance.name == "New Name"

    assert isinstance(renamed_instance.instance_dir, Path)
    assert renamed_instance.instance_dir == new_dir

    assert (new_dir / "instance.json").exists()


def test_delete_instance_removes_directory_and_registry_entry(
    temporary_paths: Path,
    fake_version
):
    instance = InstanceManager.create(
        name="Delete Test",
        version=fake_version
    )

    assert instance.instance_dir.exists()

    deleted = InstanceManager.delete_instance("Delete Test")

    assert deleted is True
    assert not instance.instance_dir.exists()
    assert InstanceManager.is_instance_exist("Delete Test") is False


def test_create_duplicate_instance_raises_error(
    temporary_paths: Path,
    fake_version
):
    InstanceManager.create(
        name="Duplicate Test",
        version=fake_version
    )

    with pytest.raises(
        RuntimeError,
        match="already exists"
    ):
        InstanceManager.create(
            name="Duplicate Test",
            version=fake_version
        )

def test_save_metadata_preserves_runtime_and_custom_fields(temporary_paths: Path, fake_version) -> None:
    instance = InstanceManager.create(name="Metadata Test", version=fake_version)
    metadata_path = instance.instance_dir / "instance.json"
    data = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
    data.update({
        "notes": "keep notes",
        "icon": "custom-icon",
        "last_played": "2026-07-15T10:00:00+00:00",
        "total_play_time_seconds": 321,
        "last_exit_code": 0,
        "custom_extension": {"enabled": True},
    })
    metadata_path.write_text(__import__("json").dumps(data), encoding="utf-8")

    InstanceManager.set_mod_loader("Metadata Test", ("fabric", "0.16.9"))

    saved = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
    assert saved["notes"] == "keep notes"
    assert saved["icon"] == "custom-icon"
    assert saved["last_played"] == "2026-07-15T10:00:00+00:00"
    assert saved["total_play_time_seconds"] == 321
    assert saved["last_exit_code"] == 0
    assert saved["custom_extension"] == {"enabled": True}
    assert saved["metadata_version"] == 2
    assert saved["mod_loader"] == ["fabric", "0.16.9"]


def test_clone_resets_runtime_history_and_play_time(temporary_paths: Path, fake_version) -> None:
    source = InstanceManager.create(name="Runtime Source", version=fake_version)
    metadata_path = source.instance_dir / "instance.json"
    data = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
    data.update({
        "last_played": "2026-07-15T12:00:00+00:00",
        "total_play_time_seconds": 999,
        "last_exit_code": 1,
        "last_launch_crashed": True,
        "last_game_log": "old.log",
        "last_crash_report": "crash.txt",
    })
    metadata_path.write_text(__import__("json").dumps(data), encoding="utf-8")
    history_path = source.instance_dir / ".mcw" / "runtime-history.json"
    history_path.parent.mkdir(parents=True)
    history_path.write_text('{"records": [{"exit_code": 1}]}', encoding="utf-8")

    cloned = InstanceManager.clone("Runtime Source", "Runtime Clone")

    cloned_data = __import__("json").loads((cloned.instance_dir / "instance.json").read_text(encoding="utf-8"))
    assert cloned_data["last_played"] == ""
    assert cloned_data["total_play_time_seconds"] == 0
    assert cloned_data["last_exit_code"] is None
    assert cloned_data["last_launch_crashed"] is False
    assert cloned_data["last_game_log"] == ""
    assert cloned_data["last_crash_report"] == ""
    assert not (cloned.instance_dir / ".mcw" / "runtime-history.json").exists()


def test_list_instances_skips_corrupted_metadata(temporary_paths: Path, fake_version) -> None:
    good = InstanceManager.create(name="Good Instance", version=fake_version)
    broken_dir = temporary_paths / "Broken Instance"
    broken_dir.mkdir()
    (broken_dir / "instance.json").write_text("{broken-json", encoding="utf-8")

    instances = InstanceManager.list_instances()

    assert [instance.name for instance in instances] == [good.name]


@pytest.mark.parametrize("name", ["CON", "nul.txt", "COM1", "LPT9", "../escape", "bad:name"])
def test_create_rejects_invalid_windows_instance_names(temporary_paths: Path, fake_version, name: str) -> None:
    with pytest.raises(RuntimeError, match="not valid on Windows"):
        InstanceManager.create(name=name, version=fake_version)


def test_list_instances_repairs_metadata_name_to_directory_name(temporary_paths: Path, fake_version) -> None:
    instance = InstanceManager.create(name="Correct Folder", version=fake_version)
    metadata_path = instance.instance_dir / "instance.json"
    data = __import__("json").loads(metadata_path.read_text(encoding="utf-8"))
    data["name"] = "Stale Name"
    metadata_path.write_text(__import__("json").dumps(data), encoding="utf-8")

    instances = InstanceManager.list_instances()

    assert [item.name for item in instances] == ["Correct Folder"]
    assert __import__("json").loads(metadata_path.read_text(encoding="utf-8"))["name"] == "Correct Folder"


def test_import_rejects_instance_name_that_escapes_instances_root(temporary_paths: Path, tmp_path: Path) -> None:
    import json
    import zipfile

    package_path = tmp_path / "unsafe-name.mcwpack"
    package_metadata = {
        "format": "mcwpack",
        "format_version": 1,
        "package_type": "instance",
        "launcher_name": "mcw-launcher",
        "launcher_version": "v0.5.1-rc.1",
        "created_at": "2026-07-16T00:00:00+00:00",
        "include_saves": False,
    }
    instance_metadata = {
        "id": "unsafe-id",
        "name": "../escape",
        "version_id": "1.20.1",
        "mod_loader": ["vanilla", "-1"],
    }
    with zipfile.ZipFile(package_path, "w") as archive:
        archive.writestr("package.json", json.dumps(package_metadata))
        archive.writestr("instance.json", json.dumps(instance_metadata))

    with pytest.raises(RuntimeError, match="not valid on Windows"):
        InstanceManager.import_instance(package_path)

    assert not (temporary_paths.parent / "escape").exists()
