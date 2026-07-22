from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisplayProfile:
    name: str
    window_width: int
    window_height: int
    minimum_width: int
    minimum_height: int
    sidebar_width: int
    right_panel_width: int
    compact: bool


FULL_HD_PROFILE = DisplayProfile(
    name="full-hd",
    window_width=1600,
    window_height=900,
    minimum_width=1280,
    minimum_height=720,
    sidebar_width=220,
    right_panel_width=400,
    compact=False,
)

HD_PROFILE = DisplayProfile(
    name="hd",
    window_width=1280,
    window_height=720,
    minimum_width=1120,
    minimum_height=640,
    sidebar_width=188,
    right_panel_width=330,
    compact=True,
)


def select_display_profile(screen_width: int, screen_height: int) -> DisplayProfile:
    width = max(1, int(screen_width))
    height = max(1, int(screen_height))

    if width >= 1920 and height >= 1080:
        return FULL_HD_PROFILE
    if width >= 1366 and height >= 768:
        return HD_PROFILE

    safe_width = max(640, min(HD_PROFILE.window_width, width - 32))
    safe_height = max(480, min(HD_PROFILE.window_height, height - 48))
    return DisplayProfile(
        name="safe-compact",
        window_width=safe_width,
        window_height=safe_height,
        minimum_width=min(960, safe_width),
        minimum_height=min(600, safe_height),
        sidebar_width=min(176, max(150, safe_width // 7)),
        right_panel_width=min(310, max(260, safe_width // 4)),
        compact=True,
    )


def fit_dialog_size(
    screen_width: int,
    screen_height: int,
    preferred_width: int,
    preferred_height: int,
    minimum_width: int = 480,
    minimum_height: int = 320,
    horizontal_margin: int = 64,
    vertical_margin: int = 48,
) -> tuple[int, int]:
    available_width = max(1, int(screen_width))
    available_height = max(1, int(screen_height))
    max_width = max(1, available_width - max(0, int(horizontal_margin)))
    max_height = max(1, available_height - max(0, int(vertical_margin)))

    width = min(max_width, max(int(minimum_width), int(preferred_width)))
    height = min(max_height, max(int(minimum_height), int(preferred_height)))
    return max(1, width), max(1, height)
