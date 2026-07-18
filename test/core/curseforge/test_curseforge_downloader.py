from pathlib import Path

import pytest

from src.core.curseforge.curseforge_downloader import CurseForgeDownloader
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


def test_unavailable_file_requires_manual_install(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not available for third-party distribution"):
        CurseForgeDownloader.download_file(make_file(is_available=False), tmp_path / "example.jar")


def test_missing_hash_is_rejected_before_download(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="does not provide a SHA-1"):
        CurseForgeDownloader.download_file(make_file(sha1=""), tmp_path / "example.jar")
