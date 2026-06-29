from src.models.minecraft.version import Version
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.core.fs.paths import Paths
from pathlib import Path
import requests
import json
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
    def load(id:str=VersionManifestManager._latest_version()) -> Version:
        """
        Default: Loading newest version of Minecraft
        """
        version_path = VersionManager._download_version(VersionManager._choosing_version(id))
        version_data = VersionManager._load_version(version_path)

        if version_path is None:
            raise RuntimeError("Cannot download version metadata")

        return VersionManager._parse_version(version_data, version_path)
    


    @staticmethod
    def _choosing_version(id:str) -> VersionManifestManager:
        versions = VersionManifestManager.get()
        ver_idx = next((i for i, version in enumerate(versions) if version.id == id),-1)
        return versions[ver_idx]

    @staticmethod
    def _download_version(version:VersionManifestManager) -> Path | None:
        version_path = Paths.version_json(version)
        version_path.parent.mkdir(parents=True,exist_ok=True)
        try:
            req = requests.get(version.url, timeout=10)
            version_path.write_text(req.text, encoding="utf-8")
            return version_path
        except requests.RequestException:
            return None
    
    @staticmethod
    def _load_version(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    @staticmethod
    def _parse_version(version_data:dict,version_path:str) -> Version | None:
        try:
            return Version(
                id=version_data["id"],
                arguments=version_data["arguments"],
                libraries=version_data["libraries"],
                downloads=version_data["downloads"],
                asset_index=version_data["assetIndex"],
                assets= version_data["assets"],
                main_class=version_data["mainClass"],
                java_version=version_data["javaVersion"],
                raw_json=version_data,
                path=version_path
            )
        except:
            return None

