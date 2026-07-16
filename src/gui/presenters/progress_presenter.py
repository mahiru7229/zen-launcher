from __future__ import annotations

from dataclasses import dataclass

from src.core.language.language_manager import tr


@dataclass(frozen=True, slots=True)
class ProgressView:
    title: str
    detail: str
    stage_text: str
    button_text: str
    percentage: int | None


class ProgressPresenter:
    _STAGE_LABELS = {
        "preparing": "PREPARING",
        "repairing_instance": "REPAIR",
        "importing_instance": "IMPORT",
        "exporting_instance": "EXPORT",
        "loading_version": "VERSION",
        "installing_mod_loader": "MOD LOADER",
        "selecting_java": "JAVA CHECK",
        "downloading_java": "JAVA DOWNLOAD",
        "installing_java": "JAVA INSTALL",
        "downloading_client": "GAME CLIENT",
        "downloading_libraries": "LIBRARIES",
        "downloading_asset_index": "ASSET INDEX",
        "downloading_assets": "ASSETS",
        "checking_mods": "MOD CHECK",
        "downloading_mods": "MODS",
        "checking_modpack": "MODPACK CHECK",
        "downloading_modpack": "MODPACK",
        "downloading_update": "LAUNCHER UPDATE",
        "building_context": "GAME DATA",
        "building_command": "COMMAND",
        "launching": "STARTING",
        "finished": "FINISHED",
    }

    _BUTTON_TEXTS = {
        "repairing_instance": "REPAIRING...",
        "importing_instance": "IMPORTING...",
        "exporting_instance": "EXPORTING...",
        "installing_mod_loader": "INSTALLING MOD LOADER...",
        "selecting_java": "CHECKING JAVA...",
        "downloading_java": "DOWNLOADING JAVA...",
        "installing_java": "INSTALLING JAVA...",
        "downloading_client": "DOWNLOADING GAME...",
        "downloading_libraries": "DOWNLOADING LIBRARIES...",
        "downloading_asset_index": "LOADING ASSETS...",
        "downloading_assets": "DOWNLOADING ASSETS...",
        "checking_mods": "CHECKING MODS...",
        "downloading_mods": "DOWNLOADING MODS...",
        "checking_modpack": "CHECKING MODPACK...",
        "downloading_modpack": "DOWNLOADING MODPACK...",
        "downloading_update": "DOWNLOADING UPDATE...",
        "building_context": "PREPARING GAME...",
        "building_command": "PREPARING LAUNCH...",
        "launching": "STARTING...",
        "finished": "STARTED",
    }

    @classmethod
    def present(cls, event: object) -> ProgressView:
        stage_value = cls._stage_value(event)
        stage_text = tr(cls._STAGE_LABELS.get(stage_value, stage_value.replace("_", " ").upper()))
        raw_title = str(getattr(event, "message", "") or stage_text.title())
        title = tr(raw_title)
        percentage = cls._percentage(event)
        detail = cls._detail(event, stage_text, percentage)
        button_text = tr(cls._BUTTON_TEXTS.get(stage_value, "WORKING..."))

        return ProgressView(
            title=title,
            detail=detail,
            stage_text=stage_text,
            button_text=button_text,
            percentage=percentage,
        )

    @staticmethod
    def _stage_value(event: object) -> str:
        stage = getattr(event, "stage", None)
        return str(getattr(stage, "value", stage or "working"))

    @staticmethod
    def _percentage(event: object) -> int | None:
        if not bool(getattr(event, "is_determinate", False)):
            return None

        raw_percentage = getattr(event, "percentage", None)

        if raw_percentage is None:
            return None

        return max(0, min(round(float(raw_percentage)), 100))

    @classmethod
    def _detail(cls, event: object, stage_text: str, percentage: int | None) -> str:
        if percentage is None:
            return stage_text.title()

        current = int(getattr(event, "current", 0) or 0)
        total = int(getattr(event, "total", 0) or 0)
        unit = getattr(event, "unit", None)
        unit_value = str(getattr(unit, "value", unit or "none"))
        quantity = cls._format_quantity(current, total, unit_value)
        parts = [quantity]
        remaining = max(total - current, 0)

        if remaining > 0:
            parts.append(cls._format_remaining(remaining, unit_value))

        speed = float(getattr(event, "bytes_per_second", 0.0) or 0.0)
        if speed > 0 and remaining > 0:
            parts.append(tr("progress.speed", speed=cls._format_bytes(round(speed))))

        parts.append(f"{percentage}%")
        return " · ".join(parts)

    @classmethod
    def _format_quantity(cls, current: int, total: int, unit: str) -> str:
        if unit == "bytes":
            return f"{cls._format_bytes(current)} / {cls._format_bytes(total)}"

        if unit == "files":
            return tr("{current} / {total} files", current=f"{current:,}", total=f"{total:,}")

        if unit == "steps":
            return tr("{current} / {total} steps", current=f"{current:,}", total=f"{total:,}")

        return f"{current:,} / {total:,}"

    @classmethod
    def _format_remaining(cls, remaining: int, unit: str) -> str:
        if unit == "bytes":
            return tr("progress.remaining_bytes", remaining=cls._format_bytes(remaining))

        if unit == "files":
            return tr("progress.remaining_files", remaining=f"{remaining:,}")

        if unit == "steps":
            return tr("progress.remaining_steps", remaining=f"{remaining:,}")

        return tr("progress.remaining_items", remaining=f"{remaining:,}")

    @staticmethod
    def _format_bytes(value: int) -> str:
        size = float(max(value, 0))

        for suffix in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or suffix == "TB":
                if suffix == "B":
                    return f"{int(size)} {suffix}"

                return f"{size:.1f} {suffix}"

            size /= 1024

        return f"{size:.1f} TB"
