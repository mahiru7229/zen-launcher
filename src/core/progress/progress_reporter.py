from src.models.progress.progress_callback import ProgressCallback
from src.models.progress.progress_event import ProgressEvent
from src.models.progress.progress_stage import ProgressStage
from src.models.progress.progress_unit import ProgressUnit


class ProgressReporter:

    def __init__(
        self,
        callback: ProgressCallback | None = None,
    ) -> None:
        self._callback = callback

    def report(
        self,
        stage: ProgressStage,
        message: str,
        current: int | None = None,
        total: int | None = None,
        unit: ProgressUnit = ProgressUnit.NONE,
        bytes_per_second: float | None = None,
    ) -> None:
        if self._callback is None:
            return

        self._callback(
            ProgressEvent(
                stage=stage,
                message=message,
                current=current,
                total=total,
                unit=unit,
                bytes_per_second=bytes_per_second,
            )
        )
    def status(
        self,
        stage: ProgressStage,
        message: str,
    ) -> None:
        self.report(
            stage=stage,
            message=message,
        )

    def bytes(
        self,
        stage: ProgressStage,
        message: str,
        current: int,
        total: int,
        bytes_per_second: float | None = None,
    ) -> None:
        self.report(
            stage=stage,
            message=message,
            current=current,
            total=total,
            unit=ProgressUnit.BYTES,
            bytes_per_second=bytes_per_second,
        )

    def files(
        self,
        stage: ProgressStage,
        message: str,
        current: int,
        total: int,
        bytes_per_second: float | None = None,
    ) -> None:
        self.report(
            stage=stage,
            message=message,
            current=current,
            total=total,
            unit=ProgressUnit.FILES,
            bytes_per_second=bytes_per_second,
        )
