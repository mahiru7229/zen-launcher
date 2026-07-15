from __future__ import annotations

from threading import Event, RLock


class DownloadPausedError(RuntimeError):
    """Raised when the user pauses the active launcher download session."""


class DownloadPauseController:
    def __init__(self) -> None:
        self._event = Event()
        self._lock = RLock()
        self._active = False

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    @property
    def is_pause_requested(self) -> bool:
        return self._event.is_set()

    def begin(self) -> None:
        with self._lock:
            self._event.clear()
            self._active = True

    def finish(self) -> None:
        with self._lock:
            self._active = False
            self._event.clear()

    def request_pause(self) -> bool:
        with self._lock:
            if not self._active:
                return False
            self._event.set()
            return True

    def raise_if_requested(self) -> None:
        if self._event.is_set():
            raise DownloadPausedError("Download paused by user.")

    def wait(self, seconds: float) -> None:
        delay = max(0.0, float(seconds))
        if self._event.wait(delay):
            raise DownloadPausedError("Download paused by user.")


def is_download_paused(error: BaseException | None) -> bool:
    current = error
    visited: set[int] = set()

    while current is not None and id(current) not in visited:
        if isinstance(current, DownloadPausedError):
            return True
        visited.add(id(current))
        current = current.__cause__ or current.__context__

    return False


download_pause_controller = DownloadPauseController()
