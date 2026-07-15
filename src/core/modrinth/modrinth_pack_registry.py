from __future__ import annotations

from pathlib import Path, PurePosixPath
import hashlib
import json

from src.models.instance.instance import Instance
from src.models.modrinth.pack_state import ModrinthManagedFileChange, ModrinthPackStateReport


class ModrinthPackRegistry:
    SCHEMA_VERSION = 3
    FILE_NAME = "modrinth-pack.json"

    @staticmethod
    def path(instance_dir: Path) -> Path:
        return Path(instance_dir) / ".mcw" / ModrinthPackRegistry.FILE_NAME

    @staticmethod
    def load(instance: Instance) -> dict:
        return ModrinthPackRegistry.load_from_dir(instance.instance_dir)

    @staticmethod
    def load_from_dir(instance_dir: Path) -> dict:
        path = ModrinthPackRegistry.path(instance_dir)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        files = data.get("managedFiles")
        if not isinstance(files, list):
            data["managedFiles"] = []
        return data

    @staticmethod
    def save(instance_dir: Path, data: dict) -> None:
        path = ModrinthPackRegistry.path(instance_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(data)
        payload["schemaVersion"] = ModrinthPackRegistry.SCHEMA_VERSION
        payload["managedFiles"] = ModrinthPackRegistry._normalize_files(payload.get("managedFiles", []))
        payload["preservedFiles"] = ModrinthPackRegistry._normalize_preserved_files(payload.get("preservedFiles", []))
        temp = path.with_suffix(path.suffix + ".part")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    @staticmethod
    def scan(instance: Instance) -> ModrinthPackStateReport:
        data = ModrinthPackRegistry.load(instance)
        changes: list[ModrinthManagedFileChange] = []
        root = Path(instance.instance_dir).resolve()
        managed_files = data.get("managedFiles", []) if isinstance(data.get("managedFiles"), list) else []

        for entry in managed_files:
            if not isinstance(entry, dict):
                continue
            relative = ModrinthPackRegistry._safe_relative(str(entry.get("path") or ""))
            if relative is None:
                continue
            target = root.joinpath(*relative.parts)
            source = str(entry.get("source") or "")
            if not target.is_file():
                changes.append(ModrinthManagedFileChange(path=relative.as_posix(), state="missing", source=source))
                continue
            expected_sha1 = str(entry.get("sha1") or "").lower()
            if expected_sha1 and ModrinthPackRegistry._sha1(target) != expected_sha1:
                changes.append(ModrinthManagedFileChange(path=relative.as_posix(), state="modified", source=source))

        return ModrinthPackStateReport(project_id=str(data.get("projectId") or ""), version_id=str(data.get("versionId") or ""), managed_files=len(managed_files), changes=tuple(changes))

    @staticmethod
    def _normalize_files(value: object) -> list[dict]:
        if not isinstance(value, list):
            return []
        normalized: dict[str, dict] = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            relative = ModrinthPackRegistry._safe_relative(str(item.get("path") or ""))
            if relative is None:
                continue
            key = relative.as_posix()
            normalized[key.casefold()] = {
                "path": key,
                "sha1": str(item.get("sha1") or "").lower(),
                "sha512": str(item.get("sha512") or "").lower(),
                "size": max(0, int(item.get("size", 0) or 0)),
                "source": str(item.get("source") or "pack"),
                "downloads": ModrinthPackRegistry._normalize_downloads(item.get("downloads", [])),
                "required": bool(item.get("required", True)),
            }
        return sorted(normalized.values(), key=lambda item: item["path"].casefold())

    @staticmethod
    def _normalize_downloads(value: object) -> list[str]:
        if not isinstance(value, (list, tuple)):
            return []
        return list(dict.fromkeys(str(url).strip() for url in value if str(url).strip()))

    @staticmethod
    def _normalize_preserved_files(value: object) -> list[dict]:
        if not isinstance(value, list):
            return []
        normalized: dict[str, dict] = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            relative = ModrinthPackRegistry._safe_relative(str(item.get("path") or ""))
            if relative is None:
                continue
            key = relative.as_posix()
            normalized[key.casefold()] = {
                "path": key,
                "reason": str(item.get("reason") or "preserved"),
                "previousSha1": str(item.get("previousSha1") or "").lower(),
                "targetSha1": str(item.get("targetSha1") or "").lower(),
            }
        return sorted(normalized.values(), key=lambda item: item["path"].casefold())

    @staticmethod
    def _safe_relative(value: str) -> PurePosixPath | None:
        normalized = str(value).replace("\\", "/").strip()
        path = PurePosixPath(normalized)
        if not normalized or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            return None
        if ":" in path.parts[0]:
            return None
        return path

    @staticmethod
    def _sha1(path: Path) -> str:
        digest = hashlib.sha1()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
