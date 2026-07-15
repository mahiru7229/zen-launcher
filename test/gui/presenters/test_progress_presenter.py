from src.gui.presenters.progress_presenter import ProgressPresenter
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage
from src.models.progress.progress_unit import ProgressUnit


def test_presenter_formats_java_byte_progress():
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_JAVA,
        message="Downloading Java 17...",
        current=5 * 1024 * 1024,
        total=20 * 1024 * 1024,
        unit=ProgressUnit.BYTES,
    )

    view = ProgressPresenter.present(event)

    assert view.title == "Downloading Java 17..."
    assert view.stage_text == "JAVA DOWNLOAD"
    assert view.button_text == "DOWNLOADING JAVA..."
    assert view.percentage == 25
    assert view.detail == "5.0 MB / 20.0 MB · 15.0 MB left · 25%"


def test_presenter_uses_indeterminate_progress_for_installation():
    event = ProgressEvent(
        stage=ProgressStage.INSTALLING_JAVA,
        message="Installing Java 17...",
    )

    view = ProgressPresenter.present(event)

    assert view.percentage is None
    assert view.stage_text == "JAVA INSTALL"
    assert view.button_text == "INSTALLING JAVA..."


def test_presenter_formats_file_progress():
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_LIBRARIES,
        message="Downloading libraries...",
        current=20,
        total=80,
        unit=ProgressUnit.FILES,
    )

    view = ProgressPresenter.present(event)

    assert view.percentage == 25
    assert view.detail == "20 / 80 files · 60 files left · 25%"


def test_presenter_formats_launcher_update_progress():
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_UPDATE,
        message="Downloading launcher update...",
        current=25,
        total=100,
        unit=ProgressUnit.BYTES,
    )

    view = ProgressPresenter.present(event)

    assert view.stage_text == "LAUNCHER UPDATE"
    assert view.button_text == "DOWNLOADING UPDATE..."
    assert view.percentage == 25


def test_presenter_formats_mod_check_progress():
    event = ProgressEvent(
        stage=ProgressStage.CHECKING_MODS,
        message="Checking Modrinth mods...",
        current=3,
        total=12,
        unit=ProgressUnit.FILES,
    )

    view = ProgressPresenter.present(event)

    assert view.stage_text == "MOD CHECK"
    assert view.button_text == "CHECKING MODS..."
    assert view.percentage == 25
    assert view.detail == "3 / 12 files · 9 files left · 25%"


def test_presenter_formats_modpack_check_progress():
    event = ProgressEvent(
        stage=ProgressStage.CHECKING_MODPACK,
        message="Checking Modrinth modpack files...",
        current=5,
        total=10,
        unit=ProgressUnit.FILES,
    )

    view = ProgressPresenter.present(event)

    assert view.stage_text == "MODPACK CHECK"
    assert view.button_text == "CHECKING MODPACK..."
    assert view.percentage == 50


def test_presenter_formats_download_speed_and_remaining_bytes():
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_MODS,
        message="Downloading example.jar...",
        current=4 * 1024 * 1024,
        total=16 * 1024 * 1024,
        unit=ProgressUnit.BYTES,
        bytes_per_second=2.5 * 1024 * 1024,
    )

    view = ProgressPresenter.present(event)

    assert view.percentage == 25
    assert view.detail == "4.0 MB / 16.0 MB · 12.0 MB left · 2.5 MB/s · 25%"


def test_presenter_hides_remaining_and_speed_after_download_completes():
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_UPDATE,
        message="Downloaded launcher update.",
        current=8 * 1024 * 1024,
        total=8 * 1024 * 1024,
        unit=ProgressUnit.BYTES,
        bytes_per_second=3 * 1024 * 1024,
    )

    view = ProgressPresenter.present(event)

    assert view.detail == "8.0 MB / 8.0 MB · 100%"


def test_presenter_shows_speed_for_active_multi_file_downloads():
    event = ProgressEvent(
        stage=ProgressStage.DOWNLOADING_LIBRARIES,
        message="Preparing Minecraft libraries...",
        current=4,
        total=10,
        unit=ProgressUnit.FILES,
        bytes_per_second=3 * 1024 * 1024,
    )

    view = ProgressPresenter.present(event)

    assert view.detail == "4 / 10 files · 6 files left · 3.0 MB/s · 40%"


def test_presenter_hides_speed_for_multi_file_checks_without_network_activity():
    event = ProgressEvent(
        stage=ProgressStage.CHECKING_MODS,
        message="Checking mods...",
        current=4,
        total=10,
        unit=ProgressUnit.FILES,
        bytes_per_second=None,
    )

    view = ProgressPresenter.present(event)

    assert view.detail == "4 / 10 files · 6 files left · 40%"
