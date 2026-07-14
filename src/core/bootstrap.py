from src.core.account.database.account_database import AccountDatabase
from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.fs.paths import Paths


def initialize_application() -> None:
    """Prepare all persistent application resources before the GUI starts."""
    Paths.initialize()
    LauncherSettingsManager().initialize()
    AccountDatabase.initialize()
