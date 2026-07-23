from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurseForgeManualDownload:
    project_id: int
    file_id: int
    project_name: str
    file_name: str
    file_size: int
    sha1: str
    project_url: str
    reason: str
