from src.core.instance.errors import InstanceAlreadyRunningError
from src.gui.presenters.launch_error_presenter import LaunchErrorPresenter


def test_presents_checksum_error():
    view = LaunchErrorPresenter.present(RuntimeError("SHA-256 mismatch for Java 17 archive."))

    assert view.title == "Download verification failed"
    assert view.status == "Download verification failed"
    assert "SHA-256 mismatch" in view.message


def test_presents_java_setup_error():
    view = LaunchErrorPresenter.present(RuntimeError("Failed to download Java 8 after 3 attempts."))

    assert view.title == "Java runtime setup failed"
    assert view.status == "Java setup failed"


def test_presents_generic_launch_error():
    view = LaunchErrorPresenter.present(RuntimeError("Unexpected command builder failure."))

    assert view.title == "Minecraft launch failed"
    assert view.status == "Launch failed"


def test_presents_instance_already_running_error():
    view = LaunchErrorPresenter.present(InstanceAlreadyRunningError("Survival"))

    assert view.title == "Instance already running"
    assert view.status == "Instance already running"
    assert "Close that game" in view.message
    assert "Survival" in view.message

def test_presents_modrinth_missing_files_with_instance_setting_hint():
    error = RuntimeError(
        "Could not download 2 required Modrinth file(s) after 3 rounds. "
        "Open Instance Settings > Modrinth downloads."
    )

    view = LaunchErrorPresenter.present(error)

    assert view.title == "Required Modrinth files are missing"
    assert view.status == "Modrinth files missing"
    assert "Instance Settings > Modrinth downloads" in view.message
    assert "Could not download 2 required Modrinth file(s)" in view.message



def test_presents_windows_path_too_long_error():
    view = LaunchErrorPresenter.present(FileNotFoundError("[WinError 206] The filename or extension is too long"))

    assert view.title == "Windows path is too long"
    assert view.status == "Windows path is too long"
    assert "C:\\MCW" in view.message
    assert "WinError 206" in view.message
