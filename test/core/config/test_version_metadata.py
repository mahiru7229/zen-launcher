from src.config import MODRINTH_USER_AGENT, VERSION, VERSION_ID, VERSION_TAG
from src.core.modrinth.modrinth_client import ModrinthClient
from src.core.package.package_manager import PackageManager
from src.gui.config import VERSION as GUI_VERSION
from src.gui.config import VERSION_ID as GUI_VERSION_ID


def test_launcher_version_metadata_has_one_source_of_truth() -> None:
    assert VERSION == "v0.5.0 Beta 10"
    assert VERSION_ID == "0.5.0-beta.10"
    assert VERSION_TAG == "v0.5.0-beta.10"
    assert GUI_VERSION == VERSION
    assert GUI_VERSION_ID == VERSION_ID
    assert PackageManager.LAUNCHER_VERSION == VERSION_TAG
    assert ModrinthClient.USER_AGENT == MODRINTH_USER_AGENT
    assert VERSION_ID in ModrinthClient.USER_AGENT
