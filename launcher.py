from src.gui.main_window_2 import run
from src.core.fs.paths import Paths
from src.core.account.database.account_database import AccountDatabase
def main() -> None:
    run()


if __name__ == "__main__":
    AccountDatabase.initialize()
    Paths.initialize()
    main()

