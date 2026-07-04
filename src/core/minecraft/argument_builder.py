from src.models.minecraft.version import Version
from src.core.minecraft.classpath_builder import ClasspathBuilder
from src.models.instance.settings import InstanceSettings
class ArgumentBuilder:
    @staticmethod
    def build(version: Version, context, settings:InstanceSettings):
        jvm_args = []
        game_args = []

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
        args = version.arguments or {}

        for arg in args.get("jvm", []):
            if isinstance(arg, str):
                jvm_args.append(ArgumentBuilder.resolve(arg, context))

        for arg in args.get("game", []):
            if isinstance(arg, str):
                game_args.append(ArgumentBuilder.resolve(arg, context))

        return jvm_args, game_args
    @staticmethod
    def resolve(value: str, context: dict):
        for k, v in context.items():
            value = value.replace("${" + k + "}", str(v))
        return value