from src.core.bootstrap import initialize_application


def main() -> None:
    initialize_application()

    # Import the GUI only after writable directories and databases are ready.
    # Some GUI controllers load account data during import/construction.
    from src.gui.main_window_2 import run

    run()


if __name__ == "__main__":
    main()
