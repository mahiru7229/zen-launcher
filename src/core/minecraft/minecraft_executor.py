from src.core.java.java_manager import JavaManager
from src.core.java.java_runtime import JavaRuntime
from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.download_manager import DownloadClientManager
from src.core.minecraft.library_manager import DownloadLibraryManager
from src.core.minecraft.asset_index_manager import AssetIndexManager
from src.core.minecraft.argument_builder import ArgumentBuilder
from src.core.fs.paths import Paths
from src.core.minecraft.asset_manager import AssetManager
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.core.minecraft.launcher_manager import LauncherManager
from src.core.minecraft.context_builder import ContextBuilder
from src.models.minecraft.version import Version
from src.models.instance.instance import Instance
from src.core.instance.settings_manager import SettingsManager
from src.models.auth.authentication import Authentication



#NEED TO CHANGE THE CORE

class MinecraftExecutor:
    @staticmethod
    def run(instance:Instance, player_data:Authentication):
        VersionManifestManager.get()
        version = VersionManager.load(instance.version_id)
        DownloadClientManager.load(version)
        DownloadLibraryManager.load(version)
        AssetManager.load(version)
        settings = SettingsManager.load(instance)
        context = ContextBuilder.build(instance,version, player_data)
        cmd = LauncherManager.build(version, context, settings)
        JavaRuntime.run(LauncherManager.select_java(), cmd)