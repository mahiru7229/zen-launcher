from __future__ import annotations

from pathlib import Path
import sys


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


def main() -> None:
    update_result = _run_update_mode()
    if update_result is not None:
        raise SystemExit(update_result)

    _start_update_cleanup()

    from src.core.bootstrap import initialize_application

    initialize_application()

    # Import the GUI only after writable directories and databases are ready.
    # Some GUI controllers load account data during import/construction.
    from src.gui.main_window_2 import run

    run()


if __name__ == "__main__":
    main()
