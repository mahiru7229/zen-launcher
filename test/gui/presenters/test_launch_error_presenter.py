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
