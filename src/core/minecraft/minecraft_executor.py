from src.core.minecraft.version_manifest_manager import VersionManifestManager
from src.core.minecraft.version_manager import VersionManager
from src.core.minecraft.download_manager import DownloadClientManager
from src.core.minecraft.library_manager import DownloadLibraryManager
from src.core.minecraft.asset_manager import AssetManager
from src.core.minecraft.launcher_manager import LauncherManager
from src.core.minecraft.context_builder import ContextBuilder
from src.core.instance.settings_manager import SettingsManager
from src.core.java.java_runtime import JavaRuntime
from src.core.java.java_selector import JavaSelector
from src.models.instance.instance import Instance
from src.models.auth.authentication import Authentication
from src.core.fs.paths import Paths

#NEED TO CHANGE THE CORE

class MinecraftExecutor:

    @staticmethod
    def run(instance: Instance, authentication: Authentication, debug_mode:bool = False) -> dict:
        VersionManifestManager.get()

        version = VersionManager.load(instance.version_id)

        DownloadClientManager.load(version)
        DownloadLibraryManager.load(version)
        AssetManager.load(version)

        settings = SettingsManager.load(instance)

        context = ContextBuilder.build(instance, version, authentication)


        


        command = LauncherManager.build(version, context, settings)

        java_version = version.java_version.get("majorVersion")

        if java_version is None:
            java_version = 8

        java = JavaSelector.select_java(java_version)

        JavaRuntime.run(java, command, instance)



        if debug_mode:
            #FOR DEBUG ONLY ====================
            native_dir = Paths.natives(version)
            print("Native directory:", native_dir)
            print("Exists:", native_dir.exists())

            if native_dir.exists():
                print("Native files:", list(native_dir.rglob("*")))
            #FOR DEBUG ONLY ====================

            
        return {
            "javaPath": java,
            "minecraftJavaMajorVersion": java_version,
            "minecraftVersion": version.id,
        }