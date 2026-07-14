from src.models.minecraft.version import Version
from src.models.instance.settings import InstanceSettings
from src.models.account.account_source import AccountSource
from src.models.account.account import Account
from src.core.minecraft.library_rule_manager import LibraryRuleManager
import shlex


class ArgumentBuilder:
    OFFLINE_MULTIPLAYER_ARGUMENTS = [
        "-Dminecraft.api.auth.host=https://nope.invalid",
        "-Dminecraft.api.account.host=https://nope.invalid",
        "-Dminecraft.api.session.host=https://nope.invalid",
        "-Dminecraft.api.services.host=https://nope.invalid",
    ]
    DEFAULT_ARGUMENT_FEATURES = {
        "is_demo_user": False,
        "has_custom_resolution": False,
        "has_quick_plays_support": False,
        "is_quick_play_singleplayer": False,
        "is_quick_play_multiplayer": False,
        "is_quick_play_realms": False,
    }

    @staticmethod
    def build(version: Version, context: dict, settings: InstanceSettings, account: Account) -> tuple[list[str], list[str]]:
        jvm_args: list[str] = [f"-Xms{settings.min_memory}M", f"-Xmx{settings.max_memory}M", *settings.jvm_arguments]
        game_args: list[str] = ["--width", str(settings.width), "--height", str(settings.height)]

        if settings.fullscreen:
            game_args.append("--fullscreen")
        game_args += settings.game_arguments

        arguments = getattr(version, "arguments", None) or {}
        minecraft_arguments = getattr(version, "minecraft_arguments", None)

        for argument in arguments.get("jvm", []):
            jvm_args.extend(ArgumentBuilder._resolve_argument_entry(argument, context))

        modern_game_arguments = arguments.get("game", [])
        if modern_game_arguments:
            for argument in modern_game_arguments:
                game_args.extend(ArgumentBuilder._resolve_argument_entry(argument, context))
        elif minecraft_arguments:
            for argument in shlex.split(minecraft_arguments, posix=False):
                game_args.append(ArgumentBuilder.resolve(argument, context))

        if minecraft_arguments:
            legacy_jvm_args = [
                f"-Djava.library.path={context['natives_directory']}",
                f"-Dminecraft.launcher.brand={context['launcher_name']}",
                f"-Dminecraft.launcher.version={context['launcher_version']}",
            ]
            for argument in legacy_jvm_args:
                if argument not in jvm_args:
                    jvm_args.append(argument)

        if account.account_type == AccountSource.OFFLINE and settings.offline_multiplayer_enabled:
            jvm_args.extend(ArgumentBuilder.OFFLINE_MULTIPLAYER_ARGUMENTS)

        return jvm_args, game_args

    @staticmethod
    def _resolve_argument_entry(argument: object, context: dict) -> list[str]:
        if isinstance(argument, str):
            return [ArgumentBuilder.resolve(argument, context)]
        if not isinstance(argument, dict):
            return []

        rules = argument.get("rules")
        if rules and not ArgumentBuilder._are_rules_allowed(rules, context):
            return []

        value = argument.get("value", [])
        values = [value] if isinstance(value, str) else value if isinstance(value, list) else []
        return [ArgumentBuilder.resolve(item, context) for item in values if isinstance(item, str)]

    @staticmethod
    def _are_rules_allowed(rules: object, context: dict) -> bool:
        if not isinstance(rules, list):
            return True

        features = dict(ArgumentBuilder.DEFAULT_ARGUMENT_FEATURES)
        context_features = context.get("argument_features", {})
        if isinstance(context_features, dict):
            features.update({str(key): bool(value) for key, value in context_features.items()})

        allowed = False
        for rule in rules:
            if not isinstance(rule, dict) or not LibraryRuleManager._is_rule_matching(rule):
                continue
            required_features = rule.get("features", {})
            if isinstance(required_features, dict) and any(features.get(str(name), False) != bool(expected) for name, expected in required_features.items()):
                continue
            allowed = rule.get("action") == "allow"

        return allowed

    @staticmethod
    def resolve(value: str, context: dict):
        for key, replacement in context.items():
            value = value.replace("${" + key + "}", str(replacement))
        return value
