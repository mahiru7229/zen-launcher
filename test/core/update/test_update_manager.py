from pathlib import Path
import zipfile

import pytest

from src.core.update.update_manager import UpdateManager


def make_zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def manager() -> UpdateManager:
    return UpdateManager("example/repo", "0.5.0-beta.2")


def test_extracts_release_zip_and_flattens_single_root_directory(tmp_path: Path) -> None:
    archive_path = tmp_path / "release.zip"
    extraction = tmp_path / "extracted"
    extraction.mkdir()
    make_zip(archive_path, {
        "MCW-Launcher/MCW Launcher.exe": b"exe",
        "MCW-Launcher/lang/en-US.json": b"{}",
    })

    manager()._extract_archive(archive_path, extraction)
    content = manager()._resolve_content_directory(extraction)

    assert content == extraction / "MCW-Launcher"
    assert (content / "MCW Launcher.exe").read_bytes() == b"exe"
    assert (content / "lang" / "en-US.json").read_bytes() == b"{}"


def test_extracts_zip_with_files_at_root_without_flattening(tmp_path: Path) -> None:
    archive_path = tmp_path / "release.zip"
    extraction = tmp_path / "extracted"
    extraction.mkdir()
    make_zip(archive_path, {"MCW Launcher.exe": b"exe", "lang/en-US.json": b"{}"})

    manager()._extract_archive(archive_path, extraction)

    assert manager()._resolve_content_directory(extraction) == extraction


@pytest.mark.parametrize("name", ["../evil.exe", "/absolute.exe", "C:/evil.exe", "folder/../../evil.exe", "..\\evil.exe"])
def test_rejects_unsafe_archive_paths(tmp_path: Path, name: str) -> None:
    archive_path = tmp_path / "release.zip"
    extraction = tmp_path / "extracted"
    extraction.mkdir()
    make_zip(archive_path, {name: b"bad"})

    with pytest.raises(RuntimeError, match="Unsafe path"):
        manager()._extract_archive(archive_path, extraction)


def test_validates_matching_update_package_manifest(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "MCW Launcher.exe").write_bytes(b"exe")
    (content / "mcw-update.json").write_text('{"schema_version": 1, "version": "0.5.0-beta.3", "executable": "MCW Launcher.exe"}', encoding="utf-8")
    from src.models.update.update_info import ReleaseAsset, UpdateInfo

    info = UpdateInfo(current_version="0.5.0-beta.2", version="0.5.0-beta.3", tag_name="v0.5.0-beta.3", title="Beta 3", release_notes="", release_url="", published_at="", prerelease=True, asset=ReleaseAsset("update.zip", "https://example.com/update.zip", 1))

    manager()._validate_package_manifest(content, info)


def test_rejects_update_package_version_mismatch(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "MCW Launcher.exe").write_bytes(b"exe")
    (content / "mcw-update.json").write_text('{"schema_version": 1, "version": "0.5.0-beta.4", "executable": "MCW Launcher.exe"}', encoding="utf-8")
    from src.models.update.update_info import ReleaseAsset, UpdateInfo

    info = UpdateInfo(current_version="0.5.0-beta.2", version="0.5.0-beta.3", tag_name="v0.5.0-beta.3", title="Beta 3", release_notes="", release_url="", published_at="", prerelease=True, asset=ReleaseAsset("update.zip", "https://example.com/update.zip", 1))

    with pytest.raises(RuntimeError, match="version mismatch"):
        manager()._validate_package_manifest(content, info)
