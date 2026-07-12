from src.models.minecraft.version import Version
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.models.instance.settings import InstanceSettings
from src.models.account.account_source import AccountSource
from src.models.auth.authentication import Authentication
from src.models.account.account import Account
import shlex





class ArgumentBuilder:
    OFFLINE_MULTIPLAYER_ARGUMENTS = [
    "-Dminecraft.api.auth.host=https://nope.invalid",
    "-Dminecraft.api.account.host=https://nope.invalid",
    "-Dminecraft.api.session.host=https://nope.invalid",
    "-Dminecraft.api.services.host=https://nope.invalid",
]

    @staticmethod
    def build(version: Version, context: dict, settings: InstanceSettings, account: Account) -> tuple[list[str], list[str]]:
        jvm_args: list[str] = []
        game_args: list[str] = []

        jvm_args += [
            f"-Xms{settings.min_memory}M",
            f"-Xmx{settings.max_memory}M",
        ]

        jvm_args += settings.jvm_arguments

        game_args += [
            "--width",
            str(settings.width),
            "--height",
            str(settings.height),
        ]

        if settings.fullscreen:
            game_args.append("--fullscreen")

        game_args += settings.game_arguments

        arguments = getattr(version, "arguments", None) or {}
        minecraft_arguments = getattr(version, "minecraft_arguments", None)

        if arguments:
            for argument in arguments.get("jvm", []):
                if isinstance(argument, str):
                    jvm_args.append(ArgumentBuilder.resolve(argument, context))

            for argument in arguments.get("game", []):
                if isinstance(argument, str):
                    game_args.append(ArgumentBuilder.resolve(argument, context))

        elif minecraft_arguments:
            legacy_game_arguments = shlex.split(minecraft_arguments, posix=False)

            for argument in legacy_game_arguments:
                game_args.append(ArgumentBuilder.resolve(argument, context))

            jvm_args += [
                f"-Djava.library.path={context['natives_directory']}",
                f"-Dminecraft.launcher.brand={context['launcher_name']}",
                f"-Dminecraft.launcher.version={context['launcher_version']}",
            ]

        if account.account_type == AccountSource.OFFLINE and settings.offline_multiplayer_enabled:
            jvm_args.extend(ArgumentBuilder.OFFLINE_MULTIPLAYER_ARGUMENTS)

        return jvm_args, game_args
    @staticmethod
    def resolve(value: str, context: dict):
        for k, v in context.items():
            value = value.replace("${" + k + "}", str(v))
        return value