from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest

from src.core.java.java_archive_downloader import JavaArchiveDownloader
from src.core.network.httpx_downloader import HttpDownloader
from src.models.java.java_release import JavaRelease


def test_java_download_uses_shared_bandwidth_limiter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"java-archive"
    release = JavaRelease(major=21, url="https://example.com/java.zip", sha256=hashlib.sha256(content).hexdigest(), size=len(content), filename="java.zip", release_name="test")
    throttled: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"Content-Length": str(len(content))}, content=content)

    monkeypatch.setattr(HttpDownloader, "_client", httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True))
    monkeypatch.setattr("src.core.java.java_archive_downloader.download_bandwidth_limiter.throttle", lambda size: throttled.append(size))

    destination = tmp_path / "java.zip"
    JavaArchiveDownloader.download(release, destination, max_retry=1)

    assert destination.read_bytes() == content
    assert sum(throttled) == len(content)
