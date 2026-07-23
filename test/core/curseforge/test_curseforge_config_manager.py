from pathlib import Path
import json

import pytest

from src.core.config.curseforge_config_manager import CurseForgeConfigManager


def test_environment_gateway_and_token_have_priority(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "curseforge.json"
    local.write_text(json.dumps({"gateway_url": "https://local.example/api/curseforge", "client_token": "local-token"}), encoding="utf-8")
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))
    monkeypatch.setenv(CurseForgeConfigManager.ENV_GATEWAY_URL, "https://environment.example/api/curseforge/")
    monkeypatch.setenv(CurseForgeConfigManager.ENV_CLIENT_TOKEN, "environment-token")

    assert CurseForgeConfigManager.gateway_url() == "https://environment.example/api/curseforge"
    assert CurseForgeConfigManager.client_token() == "environment-token"


def test_local_gateway_can_be_saved_and_loaded(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "curseforge.json"
    monkeypatch.delenv(CurseForgeConfigManager.ENV_GATEWAY_URL, raising=False)
    monkeypatch.delenv(CurseForgeConfigManager.ENV_CLIENT_TOKEN, raising=False)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))

    assert CurseForgeConfigManager.save_local("https://gateway.example/api/curseforge/", "client-token") == local
    assert CurseForgeConfigManager.gateway_url() == "https://gateway.example/api/curseforge"
    assert CurseForgeConfigManager.client_token() == "client-token"
    assert json.loads(local.read_text(encoding="utf-8")) == {
        "schema_version": 2,
        "gateway_url": "https://gateway.example/api/curseforge",
        "client_token": "client-token",
    }


def test_gateway_requires_https() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        CurseForgeConfigManager._normalize_url("http://gateway.example/api/curseforge")
