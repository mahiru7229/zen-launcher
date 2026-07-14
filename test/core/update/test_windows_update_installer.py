from src.core.update.windows_update_installer import WindowsUpdateInstaller


def test_updater_script_waits_copies_restarts_and_cleans_up() -> None:
    script = WindowsUpdateInstaller._script_text()

    assert "Wait-Process -Id $ParentPid" in script
    assert "Copy-Item" in script
    assert "-Recurse -Force" in script
    assert "Start-Process -FilePath $updatedExecutable" in script
    assert "$StagingDirectory" in script
