from dataclasses import dataclass
from src.models.minecraft.version_manifest import VersionManifest
from pathlib import Path
from datetime import datetime
import requests
import json



MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_DIR = PROJECT_ROOT / "downloads" / "manifest" 
MANIFEST_PATH = MANIFEST_DIR / "version_manifest_v2.json"

class VersionManifestManager:
    @staticmethod
    def get() -> list[VersionManifest]:
        manifest_path = VersionManifestManager._download_manifest()
        manifest_data = VersionManifestManager._load_manifest(manifest_path)
        return VersionManifestManager._parse_manifest(manifest_data)


    @staticmethod
    def _download_manifest() -> Path | None:
        MANIFEST_DIR.mkdir(exist_ok=True, parents=True)
        try:
            req = requests.get(MANIFEST_URL, timeout=10)
            MANIFEST_PATH.write_text(req.text, encoding="utf-8")
            return MANIFEST_PATH
        except requests.RequestException:
            return None


    @staticmethod
    def _load_manifest(path:Path) -> dict:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _latest_version(is_snapshot=False) -> str:
        try:
            manifest_path = VersionManifestManager._download_manifest()
            manifest_data = VersionManifestManager._load_manifest(manifest_path)
            return manifest_data["latest"]["snapshot"] if is_snapshot else manifest_data["latest"]["release"]
        except:
            return ""

    @staticmethod
    def _parse_manifest(manifest:dict) -> list[VersionManifest]:
        try:
            versions_manifest: list[VersionManifest] = []
            for version in manifest["versions"]:
                versions_manifest.extend(
                    [VersionManifest(
                        id=version["id"],
                        type = version["type"],
                        url=version["url"],
                        release_time=datetime.fromisoformat(version["releaseTime"]),
                    )]
                )
            return versions_manifest
        except:
            return []