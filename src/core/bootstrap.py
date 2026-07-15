from src.core.account.database.account_database import AccountDatabase
from src.core.config.launcher_settings_manager import LauncherSettingsManager
from src.core.fs.paths import Paths
from src.core.network.download_bandwidth_limiter import download_bandwidth_limiter
from src.core.security.account_security_manager import AccountSecurityManager


def initialize_application() -> None:
    """Prepare all persistent application resources before the GUI starts."""
    Paths.initialize()
    settings_manager = LauncherSettingsManager()
    settings_manager.initialize()
    download_bandwidth_limiter.configure_mbps(settings_manager.load().get("network", {}).get("download_limit_mbps", 0.0))
    AccountDatabase.initialize()
    AccountSecurityManager.migrate_if_needed()
