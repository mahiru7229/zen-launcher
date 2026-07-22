from pathlib import Path
import json
import subprocess
import sys
import zipfile

import pytest

from tools.build_release_zip import build_release_zip, validate_release_version


def test_validate_release_version_accepts_current_beta() -> None:
    assert validate_release_version("v0.6.0-beta.5") == "0.6.0-beta.5"


def test_validate_release_version_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        validate_release_version("0.5.1")


def test_build_release_zip_writes_update_manifest(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("readme", encoding="utf-8")
    (project / "LICENSE").write_text("license", encoding="utf-8")
    for directory in ("lang", "themes", "docs"):
        (project / directory).mkdir()
        (project / directory / "keep.txt").write_text(directory, encoding="utf-8")
    executable = tmp_path / "MCW Launcher.exe"
    executable.write_bytes(b"fake-exe")
    output = project / "release" / "MCW-Launcher-v0.6.0-beta.5-windows-x64.zip"

    build_release_zip(project, executable, "0.6.0-beta.5", output)

    with zipfile.ZipFile(output) as archive:
        root = "MCW-Launcher-v0.6.0-beta.5-windows-x64"
        manifest = json.loads(archive.read(f"{root}/mcw-update.json"))
        assert manifest["version"] == "0.6.0-beta.5"
        assert f"{root}/MCW Launcher.exe" in archive.namelist()
    assert output.with_name(f"{output.name}.sha256").is_file()


def test_release_script_runs_directly_from_any_working_directory(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    executable = tmp_path / "MCW Launcher.exe"
    executable.write_bytes(b"fake-exe")
    output = tmp_path / "MCW-Launcher-v0.6.0-beta.5-windows-x64.zip"

    result = subprocess.run([sys.executable, str(project_root / "tools" / "build_release_zip.py"), "--exe", str(executable), "--version", "0.6.0-beta.5", "--output", str(output)], cwd=tmp_path, capture_output=True, text=True, timeout=30)

    assert result.returncode == 0, result.stderr
    assert output.is_file()
    assert output.with_name(f"{output.name}.sha256").is_file()
