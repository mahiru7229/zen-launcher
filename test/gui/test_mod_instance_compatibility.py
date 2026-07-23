from pathlib import Path

from src.gui.mod_instance_compatibility import compatible_instances
from src.models.instance.instance import Instance
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def _instance(name: str, game_version: str, loader: str) -> Instance:
    return Instance(instance_id=name.lower(), name=name, version_id=game_version, instance_dir=Path(name), mod_loader=(loader, "test"))


def _version() -> ModrinthVersion:
    return ModrinthVersion(
        version_id="version",
        project_id="project",
        name="Version",
        version_number="1.0.0",
        version_type="release",
        game_versions=("1.20.1", "1.21.1"),
        loaders=("fabric",),
        files=(ModrinthFile(url="https://example.invalid/mod.jar", filename="mod.jar", sha1="a", sha512="b", size=1, primary=True),),
    )


def test_compatible_instances_require_matching_game_version_and_loader():
    instances = [
        _instance("Correct", "1.21.1", "fabric"),
        _instance("Wrong loader", "1.21.1", "forge"),
        _instance("Wrong game", "1.19.4", "fabric"),
        _instance("Also correct", "1.20.1", "fabric"),
    ]

    compatible = compatible_instances(instances, _version(), "fabric")

    assert [item.name for item in compatible] == ["Also correct", "Correct"]


def test_curseforge_file_can_use_the_same_compatible_instance_flow():
    from src.models.curseforge.file import CurseForgeFile

    file = CurseForgeFile(
        file_id=2,
        project_id=1,
        display_name="CurseForge Version",
        file_name="example.jar",
        release_type="release",
        file_date="",
        file_length=1,
        download_url="https://example.invalid/example.jar",
        sha1="a" * 40,
        game_versions=("1.20.1",),
        dependencies=(),
        loaders=("forge",),
    )
    instances = [
        _instance("Forge match", "1.20.1", "forge"),
        _instance("Fabric mismatch", "1.20.1", "fabric"),
    ]

    compatible = compatible_instances(instances, file, "forge")

    assert file.version_number == "CurseForge Version"
    assert [item.name for item in compatible] == ["Forge match"]
