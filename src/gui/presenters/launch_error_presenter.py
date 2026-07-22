from __future__ import annotations

from dataclasses import dataclass

from src.core.language.language_manager import tr
from src.core.instance.errors import InstanceAlreadyRunningError


@dataclass(frozen=True, slots=True)
class LaunchErrorView:
    title: str
    message: str
    status: str
    progress_detail: str


class LaunchErrorPresenter:
    @classmethod
    def present(cls, error: Exception) -> LaunchErrorView:
        technical_message = str(error).strip() or type(error).__name__
        normalized = technical_message.lower()

        if isinstance(error, InstanceAlreadyRunningError):
            return cls._build(
                title="Instance already running",
                summary="This instance is already being used by Minecraft. Close that game before launching the same instance again.",
                status="Instance already running",
                technical_message=technical_message,
            )

        if "required modrinth file" in normalized or ("modrinth" in normalized and "after 3 rounds" in normalized):
            return cls._build(
                title="Required Modrinth files are missing",
                summary="The launcher could not download every required Modrinth file after three rounds. Retry the launch, install the listed files manually, or open Instance Settings > Modrinth downloads for this instance to allow launch with missing files.",
                status="Modrinth files missing",
                technical_message=technical_message,
            )

        if "sha-256" in normalized or "checksum" in normalized:
            return cls._build(
                title="Download verification failed",
                summary="A downloaded file did not pass its integrity check. The launcher removed the incomplete file so it can be downloaded again safely.",
                status="Download verification failed",
                technical_message=technical_message,
            )

        if "winerror 206" in normalized or "filename or extension is too long" in normalized or "launch command or one of its paths is still too long" in normalized:
            return cls._build(
                title="Windows path is too long",
                summary="Windows rejected the Minecraft launch command or one of its paths. The launcher attempted to shorten the classpath automatically. Move MCW Launcher to a short folder such as C:\\MCW and shorten the instance name if the problem continues.",
                status="Windows path is too long",
                technical_message=technical_message,
            )

        if "no space" in normalized or "disk full" in normalized:
            return cls._build(
                title="Not enough storage",
                summary="There is not enough free disk space to finish preparing Minecraft or Java.",
                status="Not enough storage",
                technical_message=technical_message,
            )

        if "permission" in normalized or "access is denied" in normalized:
            return cls._build(
                title="File access denied",
                summary="The launcher could not write to one of its folders. Check folder permissions and whether another program is locking the file.",
                status="File access denied",
                technical_message=technical_message,
            )

        if any(keyword in normalized for keyword in ("timeout", "timed out", "connection", "network", "http error")):
            return cls._build(
                title="Network error",
                summary="The launcher could not finish the download. Check the connection and try launching again.",
                status="Network error",
                technical_message=technical_message,
            )

        if any(keyword in normalized for keyword in ("java", "adoptium", "temurin", "runtime")):
            return cls._build(
                title="Java runtime setup failed",
                summary="The launcher could not prepare the Java runtime required by this Minecraft version.",
                status="Java setup failed",
                technical_message=technical_message,
            )

        return cls._build(
            title="Minecraft launch failed",
            summary="Minecraft could not be started. The technical detail below can be used for debugging.",
            status="Launch failed",
            technical_message=technical_message,
        )

    @staticmethod
    def _build(title: str, summary: str, status: str, technical_message: str) -> LaunchErrorView:
        return LaunchErrorView(
            title=tr(title),
            message=f"{tr(summary)}\n\n{tr('Details:\n{details}', details=technical_message)}",
            status=tr(status),
            progress_detail=tr("launch.error.logs_hint"),
        )
