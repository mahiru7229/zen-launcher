from src.models.java.java import JavaInstallation
from src.models.java.java_source import JavaSource
from pathlib import Path
import subprocess
import re
import os


class JavaManager:

    @staticmethod
    def _scan_source(paths:list[Path] | None, source:JavaSource) -> list[JavaInstallation]:
        if not paths:
            return []
        javas:list[JavaInstallation]= []
        for java_path in paths:
    
            if not java_path:
                continue

            java_path_version = JavaManager._get_major_version(java_path)
            if java_path_version is None:
                continue

            javas.append(JavaInstallation(
            version=java_path_version,
            executable = java_path,
            source=source)
        )
        return javas



    @staticmethod
    def find_installation() -> list[JavaInstallation]:
        javas: list[JavaInstallation] = []

        javas.extend(JavaManager._scan_java_home())
        javas.extend(JavaManager._scan_path())

        return JavaManager._remove_duplicates(javas)
    
    @staticmethod
    def _get_java_in_java_home() -> list[Path] | None:
        java_home = os.environ.get("JAVA_HOME")
        if not java_home:
            return None
        home_path = Path(java_home)
        candidates = [
            home_path / "bin" / "java.exe",
            home_path / "java.exe",
        ] # they can return include "bin" dir, so making this crash
        for java_path in candidates:
            if java_path.is_file():
                return [java_path]
        return None
    @staticmethod
    def _get_java_in_path() -> list[Path]:
        try:
            result = subprocess.run(["where", "java"], capture_output=True, text=True, check=True, timeout=8,)

        except (subprocess.CalledProcessError, FileNotFoundError, PermissionError, OSError):
            return None

        paths = result.stdout.splitlines()

        if not paths:
            return None

        return [Path(p.strip()) for p in paths]

    @staticmethod
    def _get_major_version(java_path: Path) -> int | None:
        try:
            info = subprocess.run(
                [str(java_path), "-version"],
                capture_output=True,
                text=True,
                check=True
            )

            version_text = info.stderr.splitlines()[0]
            match = re.search(r'"([^"]+)"', version_text)

            if not match:
                return None

            version = match.group(1)

            if version.startswith("1."):
                return int(version.split(".")[1])

            return int(version.split(".")[0])



        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    @staticmethod
    def _remove_duplicates(javas: list[JavaInstallation]) -> list[JavaInstallation]:
        unique: dict[Path, JavaInstallation] = {}
        for java in javas:
            try:
                executable = java.executable.resolve(strict=False)
            except (OSError, RuntimeError):
                continue
            unique.setdefault(executable, java)
        return list(unique.values())
    


    @staticmethod
    def _scan_path() -> list[JavaInstallation]:
        
        return JavaManager._scan_source(JavaManager._get_java_in_path(), JavaSource.PATH)



    @staticmethod
    def _scan_java_home() -> list[JavaInstallation]:
        return JavaManager._scan_source(JavaManager._get_java_in_java_home(), JavaSource.JAVA_HOME)
