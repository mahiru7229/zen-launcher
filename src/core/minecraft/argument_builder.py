from src.models.minecraft.version import Version
from src.core.fs.paths import Paths
from src.core.minecraft.classpath_builder import ClasspathBuilder

class ArgumentBuilder:
    @staticmethod
    @staticmethod
    def build(version: Version, context):
        jvm_args = []
        game_args = []

        jvm_args += [
            "-Xms1G",
            "-Xmx6G",
            "-Dminecraft.realms.disabled=true"
        ]

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