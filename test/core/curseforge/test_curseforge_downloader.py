from pathlib import Path

import pytest

from src.core.curseforge.curseforge_downloader import CurseForgeDownloader, CurseForgeManualDownloadRequired
from src.models.curseforge.file import CurseForgeFile


def make_file(**overrides) -> CurseForgeFile:
    values = dict(
        file_id=2,
        project_id=1,
        display_name="Example",
        file_name="example.jar",
        release_type="release",
        file_date="",
        file_length=10,
        download_url="https://example/example.jar",
        sha1="a" * 40,
        game_versions=("1.20.1",),
        dependencies=(),
        is_available=True,
    )
    values.update(overrides)
    return CurseForgeFile(**values)


def test_unavailable_file_returns_structured_manual_requirement(tmp_path: Path) -> None:
    with pytest.raises(CurseForgeManualDownloadRequired) as captured:
        CurseForgeDownloader.download_file(make_file(is_available=False), tmp_path / "example.jar", project_name="Example")

    requirement = captured.value.requirement
    assert requirement.project_name == "Example"
    assert requirement.file_name == "example.jar"
    assert requirement.sha1 == "a" * 40
    assert "third-party distribution" in requirement.reason


def test_missing_hash_is_rejected_before_download(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="does not provide a SHA-1"):
        CurseForgeDownloader.download_file(make_file(sha1=""), tmp_path / "example.jar")


def test_missing_download_url_is_resolved_shortly_before_download(monkeypatch, tmp_path: Path) -> None:
    destination = tmp_path / "example.jar"
    calls = {}

    monkeypatch.setattr(
        "src.core.curseforge.curseforge_downloader.CurseForgeClient.get_download_url",
        staticmethod(lambda project_id, file_id, force_refresh=False: "https://cdn.example/example.jar"),
    )

    def fake_download(source, target, **kwargs):
        calls["url"] = source.download_url
        calls["target"] = target
        return target

    monkeypatch.setattr("src.core.curseforge.curseforge_downloader.HttpDownloader.download", staticmethod(fake_download))

    result = CurseForgeDownloader.download_file(make_file(download_url=""), destination)

    assert result == destination
    assert calls == {"url": "https://cdn.example/example.jar", "target": destination}


def test_forbidden_download_url_endpoint_uses_manual_fallback(monkeypatch, tmp_path: Path) -> None:
    error = RuntimeError("CurseForge returned HTTP 403.")
    setattr(error, "gateway_status", 403)

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr("src.core.curseforge.curseforge_downloader.CurseForgeClient.get_download_url", staticmethod(fail))

    with pytest.raises(CurseForgeManualDownloadRequired):
        CurseForgeDownloader.download_file(make_file(download_url="", is_available=True), tmp_path / "example.jar")
