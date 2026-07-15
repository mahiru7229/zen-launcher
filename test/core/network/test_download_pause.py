from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest

from src.core.network.download_pause import DownloadPausedError, DownloadPauseController, download_pause_controller, is_download_paused
from src.core.network.httpx_downloader import HttpDownloader


class ChunkedStream(httpx.SyncByteStream):
    def __init__(self, chunks: list[bytes], pause_after_first: bool = False) -> None:
        self._chunks = chunks
        self._pause_after_first = pause_after_first

    def __iter__(self):
        for index, chunk in enumerate(self._chunks):
            yield chunk
            if index == 0 and self._pause_after_first:
                download_pause_controller.request_pause()


@pytest.fixture(autouse=True)
def reset_pause_and_http_state():
    download_pause_controller.finish()
    HttpDownloader.close_client()
    HttpDownloader._path_locks.clear()
    yield
    download_pause_controller.finish()
    HttpDownloader.close_client()
    HttpDownloader._path_locks.clear()


def test_pause_controller_is_cooperative_and_detectable() -> None:
    controller = DownloadPauseController()
    controller.begin()

    assert controller.request_pause() is True
    with pytest.raises(DownloadPausedError) as captured:
        controller.raise_if_requested()

    wrapped = RuntimeError("wrapped")
    wrapped.__cause__ = captured.value
    assert is_download_paused(wrapped) is True

    controller.finish()
    assert controller.request_pause() is False


def test_http_download_pause_keeps_partial_and_next_launch_resumes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"abcdef"
    destination = tmp_path / "example.jar"
    info = type("Info", (), {"url": "https://example.com/example.jar", "sha1": hashlib.sha1(content).hexdigest(), "size": len(content)})()
    requests: list[str | None] = []
    phase = {"value": 1}

    class Response:
        def __init__(self, resumed: bool) -> None:
            self.status_code = 206 if resumed else 200
            self.headers = {"Content-Length": "3", "Content-Range": "bytes 3-5/6"} if resumed else {"Content-Length": "6"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self, chunk_size: int):
            if phase["value"] == 1:
                yield b"abc"
                download_pause_controller.request_pause()
                yield b"def"
                return
            yield b"def"

    class Client:
        def stream(self, method: str, url: str, *, headers: dict[str, str], timeout: float):
            requests.append(headers.get("Range"))
            return Response(resumed=phase["value"] == 2)

    monkeypatch.setattr(HttpDownloader, "get_client", lambda: Client())

    download_pause_controller.begin()
    with pytest.raises(DownloadPausedError):
        HttpDownloader.download(info, destination, max_retry=1)

    partial = destination.with_name(destination.name + ".part")
    assert partial.read_bytes() == b"abc"
    assert destination.exists() is False

    download_pause_controller.finish()
    phase["value"] = 2
    download_pause_controller.begin()
    result = HttpDownloader.download(info, destination, max_retry=1)
    download_pause_controller.finish()

    assert result.read_bytes() == content
    assert partial.exists() is False
    assert requests == [None, "bytes=3-"]
