from src.core.fs.paths import Paths
from src.models.minecraft.version import Version
from src.core.minecraft.classpath_builder import ClasspathBuilder


class ContextBuilder:

    @staticmethod
    def build(version:Version):
        classpath = ClasspathBuilder.build(
            version,
            Paths.client(version),
            Paths.libraries()
        )

        return {
            "classpath": classpath,
            "natives_directory": str(Paths.natives(version)),
            "launcher_name": "mcw-launcher",
            "launcher_version": "1.0",

            "game_directory": str(Paths.ROOT / "game"),
            "assets_root": str(Paths.assets_dir()),
            "assets_index_name": version.assets,

            "version_name": version.id,

            "auth_player_name": "Steve",
            "auth_uuid": "00000000-0000-0000-0000-000000000000",
            "auth_access_token": "0",
            "auth_xuid": "0",
            "clientid": "0",

            "version_type": version.raw_json.get("type", "release"),
        }