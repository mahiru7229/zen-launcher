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
