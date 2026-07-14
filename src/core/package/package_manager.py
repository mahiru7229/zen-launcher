import json
from datetime import datetime, UTC
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from src.models.instance.instance import Instance
from src.models.package.package_metadata import PackageMetadata
from src.core.fs.paths import Paths


class PackageManager:
    FORMAT = "mcwpack"
    FORMAT_VERSION = 1
    PACKAGE_TYPE_INSTANCE = "instance"

    LAUNCHER_NAME = "mcw-launcher"
    LAUNCHER_VERSION = "v0.5.0-beta.2"

    @staticmethod
    def create_instance_package_metadata(include_saves: bool) -> PackageMetadata:
        return PackageMetadata(
            format=PackageManager.FORMAT,
            format_version=PackageManager.FORMAT_VERSION,
            package_type=PackageManager.PACKAGE_TYPE_INSTANCE,
            launcher_name=PackageManager.LAUNCHER_NAME,
            launcher_version=PackageManager.LAUNCHER_VERSION,
            created_at=datetime.now(UTC).isoformat(),
            include_saves=include_saves,
        )

    @staticmethod
    def package_metadata_to_dict(metadata: PackageMetadata) -> dict:
        return {
            "format": metadata.format,
            "format_version": metadata.format_version,
            "package_type": metadata.package_type,
            "launcher_name": metadata.launcher_name,
            "launcher_version": metadata.launcher_version,
            "created_at": metadata.created_at,
            "include_saves": metadata.include_saves,
        }

    @staticmethod
    def load_package_metadata(archive: ZipFile) -> PackageMetadata:
        if "package.json" not in archive.namelist():
            raise RuntimeError("Invalid package: missing package.json.")

        data = json.loads(
            archive.read("package.json").decode("utf-8")
        )

        return PackageMetadata(
            format=data["format"],
            format_version=data["format_version"],
            package_type=data["package_type"],
            launcher_name=data["launcher_name"],
            launcher_version=data["launcher_version"],
            created_at=data["created_at"],
            include_saves=data["include_saves"],
        )

    @staticmethod
    def validate_package(metadata: PackageMetadata) -> None:
        if metadata.format != PackageManager.FORMAT:
            raise RuntimeError("Invalid package format.")

        if metadata.format_version > PackageManager.FORMAT_VERSION:
            raise RuntimeError("Package was created by a newer launcher.")

        if metadata.package_type != PackageManager.PACKAGE_TYPE_INSTANCE:
            raise RuntimeError("Package is not an instance package.")

    @staticmethod
    def export_instance(
        instance: Instance,
        output_path: Path,
        include_saves: bool = False
    ) -> Path:
        instance_dir = Paths.load_instance_dir(instance.name)

        if not instance_dir.exists():
            raise RuntimeError(
                f"Instance directory '{instance_dir}' does not exist."
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if output_path.suffix.lower() != ".mcwpack":
            output_path = output_path.with_suffix(".mcwpack")

        metadata = PackageManager.create_instance_package_metadata(
            include_saves
        )

        with ZipFile(
            output_path,
            "w",
            compression=ZIP_DEFLATED
        ) as archive:

            archive.writestr(
                "package.json",
                json.dumps(
                    PackageManager.package_metadata_to_dict(metadata),
                    indent=4,
                    ensure_ascii=False
                )
            )

            for path in instance_dir.rglob("*"):
                if path.is_dir():
                    continue

                if not include_saves and "saves" in path.parts:
                    continue

                archive.write(
                    path,
                    arcname=path.relative_to(instance_dir)
                )

        return output_path

    @staticmethod
    def extract(
        package_path: Path,
        output_dir: Path
    ) -> PackageMetadata:
        if not package_path.exists():
            raise RuntimeError(
                f"Package '{package_path}' does not exist."
            )

        if package_path.suffix.lower() != ".mcwpack":
            raise RuntimeError("Invalid package extension.")

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with ZipFile(package_path, "r") as archive:
            metadata = PackageManager.load_package_metadata(archive)

            PackageManager.validate_package(metadata)

            archive.extractall(output_dir)

        return metadata