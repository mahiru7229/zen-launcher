from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from time import time
from urllib.parse import quote
import hashlib
import json

import httpx

from src.core.fs.paths import Paths
from src.config import MODRINTH_USER_AGENT
from src.core.network.httpx_downloader import HttpDownloader
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthDependency, ModrinthFile, ModrinthVersion


class ModrinthClient:
    BASE_URL = "https://api.modrinth.com/v2"
    CACHE_SCHEMA = 2
    SEARCH_TTL_SECONDS = 10 * 60
    VERSIONS_TTL_SECONDS = 30 * 60
    PROJECT_TTL_SECONDS = 60 * 60
    USER_AGENT = MODRINTH_USER_AGENT

    _cache_locks: dict[Path, Lock] = {}
    _cache_locks_guard = Lock()

    @staticmethod
    def search_projects(project_type: str, query: str = "", game_version: str = "", loader: str = "fabric", index: str = "relevance", offset: int = 0, limit: int = 25, force_refresh: bool = False) -> ModrinthSearchResult:
        normalized_type = str(project_type).strip().lower()
        if normalized_type not in {"mod", "modpack"}:
            raise ValueError("Modrinth project type must be 'mod' or 'modpack'.")

        facets: list[list[str]] = [[f"project_type:{normalized_type}"]]
        if loader:
            facets.append([f"categories:{str(loader).strip().lower()}"])
        if game_version:
            facets.append([f"versions:{str(game_version).strip()}"])

        payload = ModrinthClient._get_json(
            "/search",
            params={
                "query": str(query).strip(),
                "facets": json.dumps(facets, separators=(",", ":")),
                "index": index if index in {"relevance", "downloads", "follows", "newest", "updated"} else "relevance",
                "offset": max(0, int(offset)),
                "limit": min(max(1, int(limit)), 100),
            },
            ttl=ModrinthClient.SEARCH_TTL_SECONDS,
            force_refresh=force_refresh,
        )

        if not isinstance(payload, dict):
            raise RuntimeError("Modrinth returned an invalid search response.")
        hits = payload.get("hits", [])
        if not isinstance(hits, list):
            hits = []
        projects = tuple(ModrinthClient._parse_project(item) for item in hits if isinstance(item, dict))
        return ModrinthSearchResult(projects=projects, total_hits=int(payload.get("total_hits", len(projects)) or 0), offset=int(payload.get("offset", offset) or 0), limit=int(payload.get("limit", limit) or limit))

    @staticmethod
    def get_project(project_id: str, force_refresh: bool = False) -> ModrinthProject:
        identifier = ModrinthClient._required(project_id, "Project ID")
        payload = ModrinthClient._get_json(f"/project/{quote(identifier, safe='')}", ttl=ModrinthClient.PROJECT_TTL_SECONDS, force_refresh=force_refresh)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Modrinth project '{identifier}' is unavailable.")
        return ModrinthClient._parse_project(payload)

    @staticmethod
    def list_project_versions(project_id: str, loader: str = "fabric", game_version: str = "", version_types: tuple[str, ...] | list[str] | set[str] | None = None, force_refresh: bool = False) -> list[ModrinthVersion]:
        identifier = ModrinthClient._required(project_id, "Project ID")
        params: dict[str, str] = {"include_changelog": "false"}
        if loader:
            params["loaders"] = json.dumps([str(loader).strip().lower()], separators=(",", ":"))
        if game_version:
            params["game_versions"] = json.dumps([str(game_version).strip()], separators=(",", ":"))
        payload = ModrinthClient._get_json(f"/project/{quote(identifier, safe='')}/version", params=params, ttl=ModrinthClient.VERSIONS_TTL_SECONDS, force_refresh=force_refresh)
        if not isinstance(payload, list):
            raise RuntimeError(f"Modrinth versions for '{identifier}' are unavailable.")
        versions = [ModrinthClient._parse_version(item) for item in payload if isinstance(item, dict)]
        allowed_types = ModrinthClient.normalize_version_types(version_types)
        versions = [version for version in versions if version.version_type in allowed_types]
        return sorted(versions, key=ModrinthClient._version_sort_key, reverse=True)

    @staticmethod
    def get_version(version_id: str, force_refresh: bool = False) -> ModrinthVersion:
        identifier = ModrinthClient._required(version_id, "Version ID")
        payload = ModrinthClient._get_json(f"/version/{quote(identifier, safe='')}", ttl=ModrinthClient.VERSIONS_TTL_SECONDS, force_refresh=force_refresh)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Modrinth version '{identifier}' is unavailable.")
        return ModrinthClient._parse_version(payload)

    @staticmethod
    def select_version(project_id: str, game_version: str, loader: str = "fabric", version_types: tuple[str, ...] | list[str] | set[str] | None = None) -> ModrinthVersion:
        versions = ModrinthClient.list_project_versions(project_id, loader=loader, game_version=game_version, version_types=version_types)
        if not versions:
            raise RuntimeError(f"No {loader.title()} version of this project supports Minecraft {game_version}.")
        return versions[0]


    @staticmethod
    def normalize_version_types(version_types: tuple[str, ...] | list[str] | set[str] | None = None) -> tuple[str, ...]:
        if version_types is None:
            return ("release", "beta", "alpha")
        normalized = {str(item).strip().lower() for item in version_types if str(item).strip()}
        allowed = tuple(item for item in ("release", "beta", "alpha") if item in normalized)
        return allowed or ("release",)

    @staticmethod
    def _version_sort_key(version: ModrinthVersion) -> tuple[float, int, int]:
        type_weight = {"release": 3, "beta": 2, "alpha": 1}.get(version.version_type, 0)
        return ModrinthClient._published_timestamp(version.date_published), int(version.featured), type_weight

    @staticmethod
    def _published_timestamp(value: str) -> float:
        normalized = str(value).strip()
        if not normalized:
            return 0.0
        try:
            parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()

    @staticmethod
    def _parse_project(data: dict) -> ModrinthProject:
        project_id = str(data.get("project_id") or data.get("id") or "").strip()
        return ModrinthProject(
            project_id=project_id,
            slug=str(data.get("slug") or project_id).strip(),
            title=str(data.get("title") or data.get("name") or project_id or "Unknown project").strip(),
            description=str(data.get("description") or "").strip(),
            project_type=str(data.get("project_type") or "mod").strip().lower(),
            author=str(data.get("author") or "").strip(),
            downloads=int(data.get("downloads", 0) or 0),
            icon_url=str(data.get("icon_url") or "").strip(),
            categories=tuple(str(item) for item in data.get("categories", []) if str(item).strip()),
            versions=tuple(str(item) for item in data.get("versions", []) if str(item).strip()),
            latest_version=str(data.get("latest_version") or "").strip(),
            client_side=str(data.get("client_side") or "unknown").strip().lower(),
            server_side=str(data.get("server_side") or "unknown").strip().lower(),
            date_modified=str(data.get("date_modified") or data.get("updated") or "").strip(),
        )

    @staticmethod
    def _parse_version(data: dict) -> ModrinthVersion:
        files: list[ModrinthFile] = []
        for item in data.get("files", []):
            if not isinstance(item, dict):
                continue
            hashes = item.get("hashes", {}) if isinstance(item.get("hashes"), dict) else {}
            files.append(ModrinthFile(url=str(item.get("url") or "").strip(), filename=str(item.get("filename") or "").strip(), sha1=str(hashes.get("sha1") or "").strip().lower(), sha512=str(hashes.get("sha512") or "").strip().lower(), size=int(item.get("size", 0) or 0), primary=bool(item.get("primary", False))))

        dependencies: list[ModrinthDependency] = []
        for item in data.get("dependencies", []):
            if not isinstance(item, dict):
                continue
            dependencies.append(ModrinthDependency(dependency_type=str(item.get("dependency_type") or "required").strip().lower(), project_id=str(item.get("project_id") or "").strip(), version_id=str(item.get("version_id") or "").strip(), file_name=str(item.get("file_name") or "").strip()))

        return ModrinthVersion(
            version_id=str(data.get("id") or "").strip(),
            project_id=str(data.get("project_id") or "").strip(),
            name=str(data.get("name") or data.get("version_number") or "Unknown version").strip(),
            version_number=str(data.get("version_number") or data.get("name") or "Unknown").strip(),
            version_type=str(data.get("version_type") or "release").strip().lower(),
            game_versions=tuple(str(item) for item in data.get("game_versions", []) if str(item).strip()),
            loaders=tuple(str(item).lower() for item in data.get("loaders", []) if str(item).strip()),
            files=tuple(files),
            dependencies=tuple(dependencies),
            featured=bool(data.get("featured", False)),
            date_published=str(data.get("date_published") or "").strip(),
        )

    @staticmethod
    def _get_json(path: str, params: dict[str, object] | None = None, ttl: int = 0, force_refresh: bool = False) -> object:
        normalized_params = {str(key): value for key, value in (params or {}).items() if value not in {None, ""}}
        cache_key = json.dumps({"path": path, "params": normalized_params}, sort_keys=True, separators=(",", ":"))
        cache_path = Paths.modrinth_api_cache(hashlib.sha256(cache_key.encode("utf-8")).hexdigest())

        with ModrinthClient._get_cache_lock(cache_path):
            cached = ModrinthClient._read_cache(cache_path)
            if cached is not None and not force_refresh:
                try:
                    age = time() - float(cached.get("fetchedAt", 0) or 0)
                except (TypeError, ValueError):
                    age = float("inf")
                if age <= ttl:
                    return cached.get("payload")

            client = HttpDownloader.get_client()
            try:
                response = client.get(ModrinthClient.BASE_URL + path, params=normalized_params, headers={"User-Agent": ModrinthClient.USER_AGENT}, timeout=20.0)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as error:
                if cached is not None:
                    return cached.get("payload")
                raise RuntimeError("Unable to contact Modrinth and no cached response is available.") from error

            ModrinthClient._write_cache(cache_path, payload)
            return payload

    @staticmethod
    def _get_cache_lock(path: Path) -> Lock:
        try:
            normalized = path.resolve(strict=False)
        except OSError:
            normalized = path.absolute()
        with ModrinthClient._cache_locks_guard:
            return ModrinthClient._cache_locks.setdefault(normalized, Lock())

    @staticmethod
    def _read_cache(path: Path) -> dict | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict) or data.get("schemaVersion") != ModrinthClient.CACHE_SCHEMA or "payload" not in data:
            return None
        return data

    @staticmethod
    def _write_cache(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".part")
        temp.write_text(json.dumps({"schemaVersion": ModrinthClient.CACHE_SCHEMA, "fetchedAt": time(), "payload": payload}, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    @staticmethod
    def _required(value: str, label: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError(f"{label} is required.")
        return normalized
