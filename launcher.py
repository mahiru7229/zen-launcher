from src.gui.main_window_2 import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()

# python -m PyInstaller --onefile --windowed --clean --noconfirm --collect-all PySide6 --name "MCW Launcher" launcher.py
