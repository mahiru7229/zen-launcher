from src.core.java.java_manager import JavaManager
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.core.minecraft.argument_builder import ArgumentBuilder
from src.models.minecraft.version import Version
from src.core.fs.paths import Paths
from src.models.instance.settings import InstanceSettings

class LauncherManager:
    @staticmethod
    def select_java():
        javas = JavaManager.find_installation()

        if not javas:
            raise RuntimeError("No Java found")

        return max(javas, key=lambda j: j.version).executable
    




    @staticmethod
    def build(version:Version, context, settings:InstanceSettings) -> list[str]:


        classpath = ClasspathBuilder.build(
            version,
            Paths.client(version),
            Paths.libraries()
        )

        jvm_args, game_args = ArgumentBuilder.build(version, context, settings)

        main_class = version.main_class

        cmd = [
            *jvm_args,
            "-cp",
            classpath,
            main_class,
            *game_args
        ]

        return cmd