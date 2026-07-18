from pathlib import Path
import httpx

from src.config import CURSEFORGE_USER_AGENT
from src.core.config.curseforge_config_manager import CurseForgeConfigManager
from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader


def test_search_projects_uses_forge_filters_and_api_headers(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, request=request, json={
            "data": [{
                "id": 101,
                "name": "Example",
                "slug": "example",
                "summary": "Forge mod",
                "downloadCount": 10,
                "authors": [{"name": "Mahiru"}],
                "logo": {"thumbnailUrl": "https://example/icon.png"},
                "classId": 6,
                "dateModified": "2026-01-01T00:00:00Z",
            }],
            "pagination": {"index": 0, "pageSize": 25, "totalCount": 1},
        })

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(CurseForgeConfigManager, "api_key", staticmethod(lambda: "secret"))
    monkeypatch.setattr(HttpDownloader, "get_client", classmethod(lambda cls: client))
    monkeypatch.setattr(Paths, "curseforge_api_cache", staticmethod(lambda key: tmp_path / f"{key}.json"))

    result = CurseForgeClient.search_projects("mod", query="example", game_version="1.20.1", force_refresh=True)

    request = captured["request"]
    assert request.headers["x-api-key"] == "secret"
    assert request.headers["user-agent"] == CURSEFORGE_USER_AGENT
    assert request.url.params["gameId"] == "432"
    assert request.url.params["classId"] == "6"
    assert request.url.params["modLoaderType"] == "1"
    assert request.url.params["gameVersion"] == "1.20.1"
    assert result.projects[0].project_id == 101
    assert result.projects[0].authors == ("Mahiru",)
    client.close()


def test_parse_file_includes_sha1_dependencies_and_distribution_state() -> None:
    file = CurseForgeClient._parse_file({
        "id": 22,
        "modId": 11,
        "displayName": "Example 1.0",
        "fileName": "example.jar",
        "releaseType": 2,
        "fileDate": "2026-01-01T00:00:00Z",
        "fileLength": 123,
        "downloadUrl": "https://example/example.jar",
        "hashes": [{"algo": 1, "value": "a" * 40}],
        "gameVersions": ["1.20.1", "Forge"],
        "dependencies": [{"modId": 99, "relationType": 3}],
        "isAvailable": False,
    })

    assert file.release_type == "beta"
    assert file.sha1 == "a" * 40
    assert file.dependencies[0].required is True
    assert file.is_available is False
