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
    assert view.detail == "5.0 MiB / 20.0 MiB · 25%"


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
    assert view.detail == "20 / 80 files · 25%"
