from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LaunchErrorView:
    title: str
    message: str
    status: str


class LaunchErrorPresenter:
    @classmethod
    def present(cls, error: Exception) -> LaunchErrorView:
        technical_message = str(error).strip() or type(error).__name__
        normalized = technical_message.lower()

        if "sha-256" in normalized or "checksum" in normalized:
            return cls._build(
                title="Download verification failed",
                summary="A downloaded file did not pass its integrity check. The launcher removed the incomplete file so it can be downloaded again safely.",
                status="Download verification failed",
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
            title=title,
            message=f"{summary}\n\nDetails:\n{technical_message}",
            status=status,
        )
