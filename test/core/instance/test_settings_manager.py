import json
from pathlib import Path

from src.core.instance.settings_manager import SettingsManager
from src.models.instance.instance import Instance


def make_instance(tmp_path: Path) -> Instance:
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    return Instance(instance_id="id", name="Settings", version_id="1.20.1", instance_dir=instance_dir, mod_loader=("fabric", "0.16.0"))


def test_legacy_settings_default_to_blocking_modrinth_failures(tmp_path: Path) -> None:
    instance = make_instance(tmp_path)
    (instance.instance_dir / "settings.json").write_text(json.dumps({
        "java": {"path": "", "min_memory": 1024, "max_memory": 2048, "arguments": []},
        "window": {"width": 1280, "height": 720, "fullscreen": False},
        "launch": {"game_arguments": [], "offline_multiplayer_enabled": False},
    }), encoding="utf-8")

    settings = SettingsManager.load(instance)

    assert settings.block_launch_on_modrinth_failure is True


def test_modrinth_failure_policy_is_saved_per_instance(tmp_path: Path) -> None:
    instance = make_instance(tmp_path)
    settings = SettingsManager.load(instance)
    settings.block_launch_on_modrinth_failure = False

    SettingsManager.save(instance, settings)

    saved = json.loads((instance.instance_dir / "settings.json").read_text(encoding="utf-8"))
    assert saved["launch"]["block_launch_on_modrinth_failure"] is False
    assert SettingsManager.load(instance).block_launch_on_modrinth_failure is False


def test_invalid_setting_types_fall_back_without_crashing(tmp_path: Path) -> None:
    instance = make_instance(tmp_path)
    (instance.instance_dir / "settings.json").write_text(json.dumps({
        "java": {"path": None, "min_memory": "invalid", "max_memory": -1, "arguments": "not-a-list"},
        "window": {"width": "bad", "height": 0, "fullscreen": "false"},
        "launch": {"game_arguments": None, "offline_multiplayer_enabled": "yes", "block_launch_on_modrinth_failure": "off"},
    }), encoding="utf-8")

    settings = SettingsManager.load(instance)

    assert settings.min_memory == 1024
    assert settings.max_memory == 2048
    assert settings.width == 1280
    assert settings.height == 720
    assert settings.jvm_arguments == []
    assert settings.game_arguments == []
    assert settings.fullscreen is False
    assert settings.offline_multiplayer_enabled is True
    assert settings.block_launch_on_modrinth_failure is False


def test_broken_settings_are_backed_up_and_recreated(tmp_path: Path) -> None:
    instance = make_instance(tmp_path)
    settings_path = instance.instance_dir / "settings.json"
    settings_path.write_text("{broken-json", encoding="utf-8")

    settings = SettingsManager.load(instance)

    assert settings.min_memory == 1024
    assert settings_path.is_file()
    assert (instance.instance_dir / "settings.json.broken").read_text(encoding="utf-8") == "{broken-json"
    assert json.loads(settings_path.read_text(encoding="utf-8"))["launch"]["block_launch_on_modrinth_failure"] is True


def test_save_uses_atomic_temporary_file(tmp_path: Path) -> None:
    instance = make_instance(tmp_path)
    settings = SettingsManager.load(instance)
    settings.max_memory = 4096

    SettingsManager.save(instance, settings)

    assert json.loads((instance.instance_dir / "settings.json").read_text(encoding="utf-8"))["java"]["max_memory"] == 4096
    assert not (instance.instance_dir / "settings.json.tmp").exists()


def test_loaded_memory_is_clamped_to_physical_ram(tmp_path: Path, monkeypatch) -> None:
    from src.core.system.memory import SystemMemory

    monkeypatch.setattr(SystemMemory, "total_physical_memory_mb", classmethod(lambda cls: 4096))
    instance = make_instance(tmp_path)
    (instance.instance_dir / "settings.json").write_text(json.dumps({
        "java": {"path": "", "min_memory": 8192, "max_memory": 16384, "arguments": []},
        "window": {"width": 1280, "height": 720, "fullscreen": False},
        "launch": {"game_arguments": [], "offline_multiplayer_enabled": False},
    }), encoding="utf-8")

    settings = SettingsManager.load(instance)

    assert settings.min_memory == 4096
    assert settings.max_memory == 4096


def test_saved_memory_is_clamped_to_physical_ram(tmp_path: Path, monkeypatch) -> None:
    from src.core.system.memory import SystemMemory

    monkeypatch.setattr(SystemMemory, "total_physical_memory_mb", classmethod(lambda cls: 4096))
    instance = make_instance(tmp_path)
    settings = SettingsManager.load(instance)
    settings.min_memory = 6144
    settings.max_memory = 8192

    SettingsManager.save(instance, settings)

    saved = json.loads((instance.instance_dir / "settings.json").read_text(encoding="utf-8"))
    assert saved["java"]["min_memory"] == 4096
    assert saved["java"]["max_memory"] == 4096
