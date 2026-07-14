from src.core.modloader.fabric.fabric_meta_client import FabricMetaClient
from src.core.network.httpx_downloader import HttpDownloader


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        return FakeResponse(self.responses[url])


def test_lists_loader_versions(monkeypatch):
    url = FabricMetaClient.BASE_URL + "/versions/loader/1.21.5"
    client = FakeClient({
        url: [
            {"loader": {"version": "0.19.3", "stable": True}},
            {"loader": {"version": "0.19.2", "stable": False}},
        ]
    })
    monkeypatch.setattr(HttpDownloader, "get_client", lambda: client)

    versions = FabricMetaClient.list_loader_versions("1.21.5")

    assert [version.version for version in versions] == ["0.19.3", "0.19.2"]
    assert versions[0].stable is True


def test_loads_profile(monkeypatch):
    url = FabricMetaClient.BASE_URL + "/versions/loader/1.21.5/0.19.3/profile/json"
    client = FakeClient({url: {"id": "fabric-loader", "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient"}})
    monkeypatch.setattr(HttpDownloader, "get_client", lambda: client)

    profile = FabricMetaClient.get_profile("1.21.5", "0.19.3")

    assert profile["mainClass"].endswith("KnotClient")
