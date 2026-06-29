from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Paths:
    ROOT = PROJECT_ROOT / "downloads"

    @staticmethod
    def version_dir(version):
        return Paths.ROOT / "versions" / version.id

    @staticmethod
    def client(version):
        return Paths.version_dir(version) / f"{version.id}.jar"

    @staticmethod
    def libraries():
        return Paths.ROOT / "libraries"
    
    
    @staticmethod
    def version_manifest() -> Path:
        return Paths.ROOT / "manifest" / "version_manifest_v2.json"


    @staticmethod
    def version_json(version) -> Path:
        return Paths.version_dir(version) / f"{version.id}.json"