from src.models.minecraft.version import Version
from src.models.instance.instance import Instance
from pathlib import Path
from src.core.fs.paths import Paths
import json
import shutil


class InstanceManager:

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

        instances_data = InstanceManager._load_instances_data()

        for instance in instances_data.get("instances", []):
            if instance.get("name") == instance_name:
                instance["name"] = new_name
                instance["instance_dir"] = str(new_dir)
                break

        InstanceManager._save_instances(instances_data)

        return new_dir




    @staticmethod
    def load(name: str) -> Instance:
        instance_data = InstanceManager._find_instance_data(name)

        if instance_data is None:
            raise RuntimeError(f"Instance '{name}' not found.")

        return InstanceManager._parse_instance(instance_data)

    @staticmethod
    def create(name: str, version: Version, mod_loader=("vanilla", "-1")):
        Paths.instances_root()

        if not (Paths.instances_root() / "instances.json").exists():
            Paths.instance_data_path_create()

        if InstanceManager.is_instance_exist(name):
            return

        instance = InstanceManager._add_instance(
            name,
            version,
            mod_loader
        )

        instance_data = InstanceManager._add_instances_data(
            InstanceManager._load_instances_data(),
            instance
        )

        InstanceManager._save_instances(instance_data)

    @staticmethod
    def delete_instance(name: str) -> bool:
        Paths.instances_root()

        if not (Paths.instances_root() / "instances.json").exists():
            Paths.instance_data_path_create()

        instances_data = InstanceManager._load_instances_data()

        original_count = len(instances_data["instances"])

        instances_data["instances"] = [
            inst for inst in instances_data["instances"]
            if inst.get("name") != name
        ]

        if len(instances_data["instances"]) < original_count:
            instance_dir = Paths.load_instance_dir(name)

            if instance_dir.exists():
                shutil.rmtree(instance_dir)

            InstanceManager._save_instances(instances_data)
            return True

        return False

    @staticmethod
    def is_instance_exist(name: str) -> bool:
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
            name=name,
            version_id=version.id,
            instance_dir=Paths.load_instance_dir(name),
            mod_loader=mod_loader
        )

    @staticmethod
    def _parse_instance(instance_data: dict) -> Instance:
        return Instance(
            name=instance_data.get("name"),
            version_id=instance_data.get("version_id"),
            instance_dir=Path(instance_data.get("instance_dir")),
            mod_loader=instance_data.get("mod_loader")
        )

    @staticmethod
    def _load_instances_data() -> dict:
        try:
            return json.loads(
                Paths.instance_data_path().read_text(encoding="utf-8")
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
                "name": instance_data.name,
                "version_id": instance_data.version_id,
                "instance_dir": str(instance_data.instance_dir),
                "mod_loader": instance_data.mod_loader
            }
        )

        return pre_data

    @staticmethod
    def _save_instances(data: dict):
        instance_data_path = Paths.instance_data_path()

        instance_data_path.write_text(
            json.dumps(data, indent=4),
            encoding="utf-8"
        )

        return instance_data_path