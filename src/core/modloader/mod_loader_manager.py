from src.core.modloader.fabric.fabric_version_manager import FabricVersionManager
from src.core.minecraft.version_manager import VersionManager
from src.core.progress.progress_reporter import ProgressReporter
from src.models.instance.instance import Instance
from src.models.minecraft.version import Version


class ModLoaderManager:
    VANILLA = "vanilla"
    FABRIC = "fabric"

    @staticmethod
    def load(instance: Instance, reporter: ProgressReporter | None = None) -> Version:
        loader_name, loader_version = ModLoaderManager.normalize(getattr(instance, "mod_loader", ("vanilla", "-1")))

        if loader_name == ModLoaderManager.VANILLA:
            return VersionManager.load(instance.version_id)
        if loader_name == ModLoaderManager.FABRIC:
            return FabricVersionManager.load(instance.version_id, loader_version, reporter)
        raise RuntimeError(f"Unsupported mod loader: {loader_name}")

    @staticmethod
    def prepare(version: Version, loader_name: str, loader_version: str, reporter: ProgressReporter | None = None) -> Version:
        loader_name, loader_version = ModLoaderManager.normalize((loader_name, loader_version))

        if loader_name == ModLoaderManager.VANILLA:
            return version
        if loader_name == ModLoaderManager.FABRIC:
            return FabricVersionManager.install(version, loader_version, reporter)
        raise RuntimeError(f"Unsupported mod loader: {loader_name}")

    @staticmethod
    def normalize(mod_loader: object) -> tuple[str, str]:
        if not isinstance(mod_loader, (tuple, list)) or not mod_loader:
            return ModLoaderManager.VANILLA, "-1"
        name = str(mod_loader[0]).strip().lower() or ModLoaderManager.VANILLA
        version = str(mod_loader[1]).strip() if len(mod_loader) > 1 else "-1"
        if name == ModLoaderManager.VANILLA:
            version = "-1"
        return name, version
