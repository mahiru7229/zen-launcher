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