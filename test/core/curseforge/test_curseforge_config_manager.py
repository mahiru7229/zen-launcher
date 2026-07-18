from pathlib import Path
import json

from src.core.config.curseforge_config_manager import CurseForgeConfigManager


def test_environment_api_key_has_priority(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "curseforge.json"
    local.write_text(json.dumps({"api_key": "local-key"}), encoding="utf-8")
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))
    monkeypatch.setenv(CurseForgeConfigManager.ENV_KEY, "environment-key")

    assert CurseForgeConfigManager.api_key() == "environment-key"


def test_local_api_key_can_be_saved_and_loaded(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "curseforge.json"
    monkeypatch.delenv(CurseForgeConfigManager.ENV_KEY, raising=False)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))

    assert CurseForgeConfigManager.save_local("  test-key  ") == local
    assert CurseForgeConfigManager.api_key() == "test-key"
    assert json.loads(local.read_text(encoding="utf-8")) == {"api_key": "test-key"}
