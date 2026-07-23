from __future__ import annotations

from dataclasses import dataclass, field

from src.models.curseforge.cache import CurseForgeCacheInfo


@dataclass(frozen=True, slots=True)
class CurseForgeProject:
    project_id: int
    name: str
    slug: str
    summary: str
    download_count: int
    authors: tuple[str, ...]
    logo_url: str
    class_id: int
    date_modified: str
    project_url: str = ""
    game_versions: tuple[str, ...] = ()
    loaders: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CurseForgeSearchResult:
    projects: tuple[CurseForgeProject, ...]
    total_count: int
    index: int
    page_size: int
    cache_info: CurseForgeCacheInfo = field(default_factory=CurseForgeCacheInfo)
