from pathlib import Path
from threading import Thread
from time import sleep

import httpx

from src.config import CURSEFORGE_USER_AGENT, VERSION_ID
from src.core.config.curseforge_config_manager import CurseForgeConfigManager
from src.core.curseforge.curseforge_cache import CurseForgeCache
from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.network.httpx_downloader import HttpDownloader


def configure_gateway(monkeypatch, tmp_path: Path, client: httpx.Client, token: str = "") -> None:
    monkeypatch.setattr(CurseForgeConfigManager, "gateway_url", staticmethod(lambda: "https://gateway.example/api/curseforge"))
    monkeypatch.setattr(CurseForgeConfigManager, "client_token", staticmethod(lambda: token))
    monkeypatch.setattr(HttpDownloader, "get_client", classmethod(lambda cls: client))
    monkeypatch.setattr(CurseForgeCache, "root", staticmethod(lambda: tmp_path))
    CurseForgeClient._inflight.clear()


def search_payload() -> dict:
    return {
        "data": [{
            "id": 101,
            "name": "Example",
            "slug": "example",
            "summary": "Forge mod",
            "downloadCount": 10,
            "authors": [{"name": "Mahiru"}],
            "logo": {"thumbnailUrl": "https://example/icon.png"},
            "links": {"websiteUrl": "https://www.curseforge.com/minecraft/mc-mods/example"},
            "classId": 6,
            "dateModified": "2026-01-01T00:00:00Z",
        }],
        "pagination": {"index": 0, "pageSize": 25, "totalCount": 1},
    }


def test_search_projects_uses_gateway_filters_and_safe_headers(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, request=request, json=search_payload())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    configure_gateway(monkeypatch, tmp_path, client, token="public-client-token")

    result = CurseForgeClient.search_projects("mod", query="example", game_version="1.20.1", loader="forge", force_refresh=True)

    request = captured["request"]
    assert request.url.path == "/api/curseforge/search"
    assert request.headers["user-agent"] == CURSEFORGE_USER_AGENT
    assert request.headers["x-mcw-version"] == VERSION_ID
    assert request.headers["authorization"] == "Bearer public-client-token"
    assert "x-api-key" not in request.headers
    assert request.url.params["query"] == "example"
    assert request.url.params["classId"] == "6"
    assert request.url.params["loader"] == "forge"
    assert request.url.params["gameVersion"] == "1.20.1"
    assert result.projects[0].project_id == 101
    assert result.projects[0].authors == ("Mahiru",)
    assert result.projects[0].project_url.endswith("/example")
    assert result.cache_info.from_cache is False
    client.close()


def test_fresh_search_cache_avoids_a_second_gateway_request(monkeypatch, tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request, json=search_payload())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    configure_gateway(monkeypatch, tmp_path, client)

    first = CurseForgeClient.search_projects("mod", query="example", game_version="1.20.1", loader="forge")
    second = CurseForgeClient.search_projects("mod", query="example", game_version="1.20.1", loader="forge")

    assert calls == 1
    assert first.cache_info.from_cache is False
    assert second.cache_info.from_cache is True
    client.close()


def test_identical_concurrent_requests_are_coalesced(monkeypatch, tmp_path: Path) -> None:
    calls = 0
    results = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        sleep(0.05)
        return httpx.Response(200, request=request, json=search_payload())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    configure_gateway(monkeypatch, tmp_path, client)

    def run() -> None:
        results.append(CurseForgeClient.search_projects("mod", query="example", game_version="1.20.1", loader="forge", force_refresh=True))

    threads = [Thread(target=run), Thread(target=run)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls == 1
    assert len(results) == 2
    client.close()


def test_parse_file_includes_sha1_dependencies_loader_and_distribution_state() -> None:
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
        "gameVersions": ["1.20.1", "Forge", "Java 17", "Client"],
        "dependencies": [{"modId": 99, "relationType": 3}],
        "isAvailable": False,
    })

    assert file.release_type == "beta"
    assert file.sha1 == "a" * 40
    assert file.dependencies[0].required is True
    assert file.is_available is False
    assert file.game_versions == ("1.20.1",)
    assert file.loaders == ("forge",)


def test_gateway_failure_returns_stale_cache_with_error_state(monkeypatch, tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, request=request, json=search_payload())
        return httpx.Response(
            503,
            request=request,
            json={"error": {"code": "UPSTREAM_UNAVAILABLE", "message": "CurseForge is unavailable."}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    configure_gateway(monkeypatch, tmp_path, client)

    first = CurseForgeClient.search_projects("mod", query="example", game_version="1.20.1", loader="forge")
    fallback = CurseForgeClient.search_projects(
        "mod",
        query="example",
        game_version="1.20.1",
        loader="forge",
        force_refresh=True,
    )

    assert calls == 2
    assert first.cache_info.from_cache is False
    assert fallback.cache_info.from_cache is True
    assert fallback.projects[0].project_id == 101
    assert CurseForgeClient.cache_status().last_error == "CurseForge is unavailable."
    client.close()


def test_curseforge_file_works_with_shared_instance_compatibility_flow() -> None:
    from pathlib import Path

    from src.gui.mod_instance_compatibility import compatible_instances
    from src.models.instance.instance import Instance

    file = CurseForgeClient._parse_file({
        "id": 22,
        "modId": 11,
        "displayName": "Example Forge Build",
        "fileName": "example.jar",
        "releaseType": 1,
        "fileLength": 123,
        "downloadUrl": "https://example.invalid/example.jar",
        "hashes": [{"algo": 1, "value": "a" * 40}],
        "gameVersions": ["1.20.1", "Forge", "Java 17"],
    })
    instances = [
        Instance(instance_id="match", name="Match", version_id="1.20.1", instance_dir=Path("Match"), mod_loader=("forge", "47.4.0")),
        Instance(instance_id="loader", name="Wrong loader", version_id="1.20.1", instance_dir=Path("Wrong loader"), mod_loader=("fabric", "0.16.0")),
        Instance(instance_id="game", name="Wrong game", version_id="1.21.1", instance_dir=Path("Wrong game"), mod_loader=("forge", "52.0.0")),
    ]

    result = compatible_instances(instances, file, "forge")

    assert file.version_number == "Example Forge Build"
    assert file.game_versions == ("1.20.1",)
    assert [instance.name for instance in result] == ["Match"]


def test_catalog_search_filters_projects_by_latest_file_loader(monkeypatch, tmp_path: Path) -> None:
    payload = {
        "data": [
            {
                "id": 101,
                "name": "Forge only",
                "slug": "forge-only",
                "latestFilesIndexes": [
                    {"gameVersion": "1.20.1", "fileId": 1, "modLoader": 1},
                ],
            },
            {
                "id": 102,
                "name": "Fabric only",
                "slug": "fabric-only",
                "latestFilesIndexes": [
                    {"gameVersion": "1.20.1", "fileId": 2, "modLoader": 4},
                ],
            },
        ],
        "pagination": {"index": 0, "pageSize": 25, "totalCount": 2},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        # Project search cannot send loader without a game version, so the
        # launcher must filter this page using latestFilesIndexes.
        assert "loader" not in request.url.params
        return httpx.Response(200, request=request, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    configure_gateway(monkeypatch, tmp_path, client)

    result = CurseForgeClient.search_projects("mod", query="hunter", loader="fabric", force_refresh=True)

    assert [project.project_id for project in result.projects] == [102]
    assert result.projects[0].loaders == ("fabric",)
    assert result.projects[0].game_versions == ("1.20.1",)
    client.close()


def test_catalog_file_list_sends_loader_without_game_version(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, request=request, json={"data": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    configure_gateway(monkeypatch, tmp_path, client)

    result = CurseForgeClient.list_files_result(1515343, loader="forge", force_refresh=True)

    assert result.files == ()
    assert captured["request"].url.params["loader"] == "forge"
    assert "gameVersion" not in captured["request"].url.params
    client.close()
