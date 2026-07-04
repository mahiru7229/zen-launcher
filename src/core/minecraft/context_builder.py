from src.core.fs.paths import Paths
from src.models.minecraft.version import Version
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.models.instance.instance import Instance
from src.models.auth.authentication import Authentication
from pathlib import Path


class ContextBuilder:

    @staticmethod
    def build(instance:Instance,version:Version, player_data:Authentication):
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

            "game_directory": str(Path(instance.instance_dir)),
            "assets_root": str(Paths.assets_dir()),
            "assets_index_name": version.assets,

            "version_name": version.id,

            "auth_player_name": player_data.player_name,
            "auth_uuid": player_data.uuid,
            "auth_access_token": player_data.access_token,
            "auth_xuid": player_data.xuid,
            "clientid": player_data.client_id,

            "version_type": version.raw_json.get("type", "release"),
        }