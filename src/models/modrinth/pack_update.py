from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModrinthPackUpdateInfo:
    project_id: str
    pack_name: str
    current_version_id: str
    current_version_number: str
    target_version_id: str
    target_version_number: str
    target_version_type: str
    target_date_published: str

    @property
    def available(self) -> bool:
        return bool(self.target_version_id and self.target_version_id != self.current_version_id)


@dataclass(frozen=True, slots=True)
class ModrinthPackUpdateResult:
    instance_name: str
    pack_name: str
    previous_version: str
    target_version: str
    added_files: int
    replaced_files: int
    removed_files: int
    preserved_files: tuple[str, ...]
    backup_path: Path
