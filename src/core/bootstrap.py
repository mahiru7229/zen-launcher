from src.core.account.database.account_database import AccountDatabase
from src.core.fs.paths import Paths


def initialize_application() -> None:
    """Prepare all persistent application resources before the GUI starts."""
    Paths.initialize()
    AccountDatabase.initialize()
