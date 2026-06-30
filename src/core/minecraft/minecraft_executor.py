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


class MinecraftExecutor:
    @staticmethod
    def run(version):
        VersionManifestManager.get()
        VersionManager.load(version.id)
        DownloadClientManager.load(version)
        DownloadLibraryManager.load(version)
        AssetManager.load(version)
        context = ContextBuilder.build(version)
        cmd = LauncherManager.build(version, context)
        JavaRuntime.run(LauncherManager.select_java(), cmd)