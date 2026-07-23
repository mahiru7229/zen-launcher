from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import tempfile
import traceback


def _run_update_mode() -> int | None:
    if len(sys.argv) < 2 or sys.argv[1] != "--apply-update":
        return None
    if len(sys.argv) != 3:
        return 2

    from src.core.update.update_applier import run_update_applier

    return run_update_applier(Path(sys.argv[2]))


def _start_update_cleanup() -> None:
    from src.core.update.update_cleanup import UpdateCleanupWorker, consume_update_cleanup_arguments

    cleaned_arguments, cleanup_request = consume_update_cleanup_arguments(sys.argv)
    sys.argv = cleaned_arguments
    if cleanup_request is not None:
        UpdateCleanupWorker(cleanup_request).start()


def _write_startup_error(error: BaseException, stage_key: str = "startup.starting", traceback_text: str | None = None) -> Path | None:
    payload = (
        f"MCW Launcher startup failure\n"
        f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Stage: {stage_key}\n"
        f"Error: {type(error).__name__}: {error}\n\n"
        f"{traceback_text or traceback.format_exc()}"
    )

    candidate_directories: list[Path] = []
    try:
        from src.core.fs.paths import Paths

        candidate_directories.append(Paths.LOGS_ROOT)
    except Exception:
        pass

    candidate_directories.append(Path(tempfile.gettempdir()) / "MCW Launcher")
    for directory in candidate_directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / "startup-error.log"
            path.write_text(payload, encoding="utf-8")
            return path
        except OSError:
            continue
    return None


def main() -> None:
    update_result = _run_update_mode()
    if update_result is not None:
        raise SystemExit(update_result)

    _start_update_cleanup()

    from src.gui.application import create_application
    from src.gui.startup_splash import StartupSplash

    app = create_application(sys.argv)
    splash = StartupSplash()
    splash.show()
    splash.update_progress(2, "startup.starting")
    startup_stage_key = "startup.starting"

    try:
        from src.core.bootstrap import initialize_application
        from src.core.startup_runner import run_startup_task

        def update_startup_progress(percent: int, message_key: str) -> None:
            nonlocal startup_stage_key
            startup_stage_key = str(message_key)
            splash.update_progress(percent, startup_stage_key)

        settings = run_startup_task(initialize_application, update_startup_progress, app.processEvents)

        from src.core.language.language_manager import language_manager, tr

        language_manager.reload()
        language_manager.set_language(settings.get("gui", {}).get("language", "en-US"), notify=False)
        splash.retranslate()
        startup_stage_key = "startup.loading_interface"
        splash.update_progress(93, startup_stage_key)

        # Import and construct Qt widgets only on the GUI thread. Persistent I/O
        # above is isolated so a locked database cannot freeze the splash forever.
        from src.gui.main_window_2 import MainWindow

        window = MainWindow()
        startup_stage_key = "startup.finalizing"
        splash.update_progress(99, startup_stage_key)
        window.show()
        app.processEvents()
        startup_stage_key = "startup.ready"
        splash.update_progress(100, startup_stage_key, "startup.ready_detail")
        splash.finish(window)
    except Exception as error:
        from PySide6.QtWidgets import QMessageBox
        from src.core.language.language_manager import tr
        from src.core.startup_runner import StartupWorkerError

        traceback_text = error.traceback_text if isinstance(error, StartupWorkerError) else traceback.format_exc()
        error_path = _write_startup_error(error, startup_stage_key, traceback_text)
        splash.show_error()
        splash.raise_()
        splash.activateWindow()
        path_text = str(error_path) if error_path is not None else tr("startup.error_log_unavailable")
        stage_text = tr(startup_stage_key)
        QMessageBox.critical(splash, tr("startup.failed_title"), tr("startup.failed_message", error=error, stage=stage_text, path=path_text))
        splash.close()
        raise SystemExit(1) from None

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
