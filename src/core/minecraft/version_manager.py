from src.models.minecraft.version import Version
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from pathlib import Path
#dict_keys(
# ['arguments',
#  'assetIndex',
#  'assets',
#  'complianceLevel',
#  'downloads', 'id',
#  'javaVersion',
#  'libraries',
#  'logging',
#  'mainClass',
#  'minimumLauncherVersion',
#  'releaseTime',
#  'time',
#  'type'])



class VersionManager:
    @staticmethod
    def load() -> Version:
        ...

    @staticmethod
    def _choosing_version(id:str=VersionManifestManager._latest_version()) -> VersionManifestManager:
        versions = VersionManifestManager.get()
        ver_idx = next((i for i, version in enumerate(versions) if version.id == id),-1)
        return versions[ver_idx]

    @staticmethod
    def _download_version() -> Path | None:
        ...
    
    @staticmethod
    def _load_version() -> dict:
        ...
    @staticmethod
    def _parse_version() -> Version:
        ...

