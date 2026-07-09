from src.models.minecraft.version import Version
from src.models.instance.instance import Instance
from src.core.fs.paths import Paths
from src.core.package.package_manager import PackageManager

from pathlib import Path
import json
import shutil
import uuid


class InstanceManager:

    @staticmethod
    def _save_instance_metadata(instance: Instance) -> None:
        path = Paths.instance_metadata(instance.name)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        path.write_text(
            json.dumps(
                {
                    "id": instance.instance_id,
                    "name": instance.name,
                    "version_id": instance.version_id,
                    "mod_loader": instance.mod_loader,

                    "created_at": "",
                    "updated_at": "",
                    "last_played": "",

                    "icon": "grass_block",
                    "notes": "",

                    "launcher_version": "v0.2.2-alpha",
                    "metadata_version": 1
                },
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    @staticmethod
    def _load_instance_metadata(path: Path) -> Instance:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        return Instance(
            instance_id=data["id"],
            name=data["name"],
            version_id=data["version_id"],
            mod_loader=data["mod_loader"],
        )

    @staticmethod
    def list_instances() -> list[Instance]:
        instances: list[Instance] = []

        root = Paths.instances_root()

        for instance_dir in root.iterdir():
            if not instance_dir.is_dir():
                continue

            metadata_path = instance_dir / "instance.json"

            if not metadata_path.exists():
                continue

            instance = InstanceManager._load_instance_metadata(metadata_path)
            instances.append(instance)

        return instances

    @staticmethod
    def clone(
        source_name: str,
        new_name: str,
        include_saves: bool = False
    ) -> Instance:
        if not InstanceManager.is_instance_exist(source_name):
            raise RuntimeError(
                f"Instance '{source_name}' does not exist."
            )

        if InstanceManager.is_instance_exist(new_name):
            raise RuntimeError(
                f"Instance '{new_name}' already exists."
            )

        source_dir = Paths.load_instance_dir(source_name)
        target_dir = Paths.load_instance_dir(new_name)

        ignore = None

        if not include_saves:
            ignore = shutil.ignore_patterns(
                "saves",
                "logs",
                "crash-reports"
            )

        shutil.copytree(
            source_dir,
            target_dir,
            ignore=ignore
        )

        instance = InstanceManager.load(new_name)

        instance.instance_id = str(uuid.uuid4())
        instance.name = new_name

        InstanceManager._save_instance_metadata(instance)

        instances_data = InstanceManager._add_instances_data(
            InstanceManager._load_instances_data(),
            instance
        )
        InstanceManager._save_instances(instances_data)

        return instance

    @staticmethod
    def export(
        instance_name: str,
        output_path: Path,
        include_saves: bool = False
    ) -> Path:
        instance = InstanceManager.load(instance_name)

        return PackageManager.export_instance(
            instance,
            output_path,
            include_saves
        )

    @staticmethod
    def import_instance(package_path: Path) -> Instance:
        temp_dir = Paths.instances_root() / "_import_temp"

        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        temp_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        try:
            PackageManager.extract(
                package_path,
                temp_dir
            )

            metadata_files = list(
                temp_dir.rglob("instance.json")
            )

            if len(metadata_files) != 1:
                raise RuntimeError(
                    "Invalid package: missing or duplicated instance.json."
                )

            metadata_path = metadata_files[0]
            imported_dir = metadata_path.parent

            instance = InstanceManager._load_instance_metadata(
                metadata_path
            )

            if InstanceManager.is_instance_exist(instance.name):
                raise RuntimeError(
                    f"Instance '{instance.name}' already exists."
                )

            target_dir = Paths.load_instance_dir(instance.name)

            shutil.move(
                str(imported_dir),
                str(target_dir)
            )

            instances_data = InstanceManager._add_instances_data(
                InstanceManager._load_instances_data(),
                instance
            )
            InstanceManager._save_instances(instances_data)

            return instance

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    @staticmethod
    def rename(instance_name: str, new_name: str) -> Path:
        if not InstanceManager.is_instance_exist(instance_name):
            raise RuntimeError(
                f"Instance '{instance_name}' does not exist!"
            )

        if InstanceManager.is_instance_exist(new_name):
            raise RuntimeError(
                f"Instance '{new_name}' already exists!"
            )

        if instance_name == new_name:
            return Paths.load_instance_dir(instance_name)

        old_dir = Paths.load_instance_dir(instance_name)
        new_dir = Paths.load_instance_dir(new_name)

        old_dir.rename(new_dir)

        instance = InstanceManager.load(new_name)
        instance.name = new_name

        InstanceManager._save_instance_metadata(instance)

        instances_data = InstanceManager._load_instances_data()

        for item in instances_data.get("instances", []):
            if item.get("name") == instance_name:
                item["name"] = new_name
                break

        InstanceManager._save_instances(instances_data)

        return new_dir

    @staticmethod
    def load(name: str) -> Instance:
        instance_dir = Paths.load_instance_dir(name)
        metadata_path = instance_dir / "instance.json"

        if metadata_path.exists():
            return InstanceManager._load_instance_metadata(metadata_path)

        instance_data = InstanceManager._find_instance_data(name)

        if instance_data is None:
            raise RuntimeError(
                f"Instance '{name}' not found."
            )

        instance = InstanceManager._parse_instance(instance_data)

        InstanceManager._migrate_instance(instance)

        return instance

    @staticmethod
    def _migrate_instance(instance: Instance) -> None:
        InstanceManager._save_instance_metadata(instance)

    @staticmethod
    def create(
        name: str,
        version: Version,
        mod_loader=("vanilla", "-1")
    ) -> Instance:
        if InstanceManager.is_instance_exist(name):
            raise RuntimeError(
                f"Instance '{name}' already exists."
            )

        Paths.instances_root()
        Paths.instance_data_path_create()
        Paths.create_instance_dir(name)

        instance = InstanceManager._add_instance(
            name,
            version,
            mod_loader
        )

        instances_data = InstanceManager._add_instances_data(
            InstanceManager._load_instances_data(),
            instance
        )
        InstanceManager._save_instances(instances_data)

        InstanceManager._save_instance_metadata(instance)

        return instance

    @staticmethod
    def delete_instance(name: str) -> bool:
        if not InstanceManager.is_instance_exist(name):
            return False

        instance_dir = Paths.load_instance_dir(name)

        if instance_dir.exists():
            shutil.rmtree(instance_dir)

        Paths.instances_root()
        Paths.instance_data_path_create()

        instances_data = InstanceManager._load_instances_data()

        instances_data["instances"] = [
            inst for inst in instances_data.get("instances", [])
            if inst.get("name") != name
        ]

        InstanceManager._save_instances(instances_data)

        return True

    @staticmethod
    def is_instance_exist(name: str) -> bool:
        metadata_path = Paths.instance_metadata(name)

        if metadata_path.exists():
            return True

        return InstanceManager._find_instance_data(name) is not None

    @staticmethod
    def _find_instance_data(name: str) -> dict | None:
        instances_data = InstanceManager._load_instances_data()

        for instance in instances_data.get("instances", []):
            if instance.get("name") == name:
                return instance

        return None

    @staticmethod
    def _add_instance(
        name: str,
        version: Version,
        mod_loader: tuple
    ) -> Instance:
        return Instance(
            instance_id=str(uuid.uuid4()),
            name=name,
            version_id=version.id,
            mod_loader=mod_loader
        )

    @staticmethod
    def _parse_instance(instance_data: dict) -> Instance:
        return Instance(
            instance_id=instance_data.get("id")
            or instance_data.get("instance_id")
            or str(uuid.uuid4()),
            name=instance_data.get("name"),
            version_id=instance_data.get("version_id"),
            mod_loader=instance_data.get("mod_loader")
        )

    @staticmethod
    def _load_instances_data() -> dict:
        try:
            return json.loads(
                Paths.instance_data_path().read_text(
                    encoding="utf-8"
                )
            )
        except (FileNotFoundError, json.JSONDecodeError):
            return {"instances": []}

    @staticmethod
    def _add_instances_data(
        pre_data: dict,
        instance_data: Instance
    ) -> dict:
        if "instances" not in pre_data:
            pre_data["instances"] = []

        pre_data["instances"].append(
            {
                "id": instance_data.instance_id,
                "name": instance_data.name,
                "version_id": instance_data.version_id,
                "mod_loader": instance_data.mod_loader
            }
        )

        return pre_data

    @staticmethod
    def _save_instances(data: dict) -> Path:
        instance_data_path = Paths.instance_data_path()

        instance_data_path.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        return instance_data_path