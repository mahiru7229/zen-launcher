from __future__ import annotations

from dataclasses import dataclass


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


@dataclass(frozen=True, slots=True)
class CurseForgeSearchResult:
    projects: tuple[CurseForgeProject, ...]
    total_count: int
    index: int
    page_size: int
