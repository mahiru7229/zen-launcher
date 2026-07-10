from src.core.java.java_manager import JavaManager
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.core.minecraft.argument_builder import ArgumentBuilder
from src.models.minecraft.version import Version
from src.core.fs.paths import Paths
from src.models.auth.authentication import Authentication
from src.models.instance.settings import InstanceSettings
from src.models.account.account import Account
class LauncherManager:

    @staticmethod
    def build(version:Version, context, settings:InstanceSettings, account:Account) -> list[str]:


        classpath = ClasspathBuilder.build(
            version,
            Paths.client(version),
            Paths.libraries()
        )

        jvm_args, game_args = ArgumentBuilder.build(version, context, settings,account)
        #FOR DEBUG ONLY ===========
        print(settings.offline_multiplayer_enabled, account.account_type)
        #FOR DEBUG ONLY ===========
        main_class = version.main_class

        cmd = [
            *jvm_args,
            "-cp",
            classpath,
            main_class,
            *game_args
        ]

        return cmd