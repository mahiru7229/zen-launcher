from __future__ import annotations

from pathlib import Path
from time import time
import hashlib
import json

import httpx

from src.config import CURSEFORGE_USER_AGENT
from src.core.config.curseforge_config_manager import CurseForgeConfigManager
from src.core.fs.paths import Paths
from src.core.network.httpx_downloader import HttpDownloader
from src.models.curseforge.file import CurseForgeDependency, CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult


class CurseForgeClient:
    BASE_URL = "https://api.curseforge.com/v1"
    MINECRAFT_GAME_ID = 432
    CLASS_MODS = 6
    CLASS_MODPACKS = 4471
    MOD_LOADER_FORGE = 1
    CACHE_TTL_SECONDS = 10 * 60

    @staticmethod
    def is_available() -> bool:
        return CurseForgeConfigManager.is_configured()

    @staticmethod
    def require_api_key() -> str:
        key = CurseForgeConfigManager.api_key()
        if not key:
            raise RuntimeError(
                "CurseForge integration needs an API key. Set MCW_CURSEFORGE_API_KEY or create config/curseforge.json with an api_key value."
            )
        return key

    @staticmethod
    def search_projects(project_type: str, query: str = "", game_version: str = "", index: int = 0, page_size: int = 25, sort: str = "popularity", force_refresh: bool = False) -> CurseForgeSearchResult:
        kind = str(project_type).strip().lower()
        if kind not in {"mod", "modpack"}:
            raise ValueError("CurseForge project type must be 'mod' or 'modpack'.")
        class_id = CurseForgeClient.CLASS_MODS if kind == "mod" else CurseForgeClient.CLASS_MODPACKS
        sort_field = {"popularity": 2, "updated": 3, "newest": 11, "downloads": 6}.get(str(sort).lower(), 2)
        params: dict[str, object] = {
            "gameId": CurseForgeClient.MINECRAFT_GAME_ID,
            "classId": class_id,
            "modLoaderType": CurseForgeClient.MOD_LOADER_FORGE,
            "searchFilter": str(query).strip(),
            "sortField": sort_field,
            "sortOrder": "desc",
            "index": max(0, int(index)),
            "pageSize": min(max(1, int(page_size)), 50),
        }
        if game_version:
            params["gameVersion"] = str(game_version).strip()
        payload = CurseForgeClient._get_json("/mods/search", params=params, ttl=CurseForgeClient.CACHE_TTL_SECONDS, force_refresh=force_refresh)
        data = payload.get("data", []) if isinstance(payload, dict) else []
        pagination = payload.get("pagination", {}) if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict) else {}
        projects = tuple(CurseForgeClient._parse_project(item) for item in data if isinstance(item, dict))
        return CurseForgeSearchResult(projects=projects, total_count=int(pagination.get("totalCount", len(projects)) or 0), index=int(pagination.get("index", index) or 0), page_size=int(pagination.get("pageSize", page_size) or page_size))

    @staticmethod
    def get_project(project_id: int | str, force_refresh: bool = False) -> CurseForgeProject:
        identifier = CurseForgeClient._positive_int(project_id, "Project ID")
        payload = CurseForgeClient._get_json(f"/mods/{identifier}", ttl=30 * 60, force_refresh=force_refresh)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(f"CurseForge project {identifier} is unavailable.")
        return CurseForgeClient._parse_project(data)

    @staticmethod
    def list_files(project_id: int | str, game_version: str = "", release_types: tuple[str, ...] | list[str] | set[str] | None = None, page_size: int = 50, force_refresh: bool = False) -> list[CurseForgeFile]:
        identifier = CurseForgeClient._positive_int(project_id, "Project ID")
        params: dict[str, object] = {"modLoaderType": CurseForgeClient.MOD_LOADER_FORGE, "pageSize": min(max(1, int(page_size)), 50), "index": 0}
        if game_version:
            params["gameVersion"] = str(game_version).strip()
        payload = CurseForgeClient._get_json(f"/mods/{identifier}/files", params=params, ttl=20 * 60, force_refresh=force_refresh)
        data = payload.get("data", []) if isinstance(payload, dict) else []
        allowed = set(CurseForgeClient.normalize_release_types(release_types))
        files = [CurseForgeClient._parse_file(item) for item in data if isinstance(item, dict)]
        files = [item for item in files if item.release_type in allowed]
        return sorted(files, key=lambda item: item.file_date, reverse=True)

    @staticmethod
    def get_file(project_id: int | str, file_id: int | str, force_refresh: bool = False) -> CurseForgeFile:
        project = CurseForgeClient._positive_int(project_id, "Project ID")
        file_identifier = CurseForgeClient._positive_int(file_id, "File ID")
        payload = CurseForgeClient._get_json(f"/mods/{project}/files/{file_identifier}", ttl=30 * 60, force_refresh=force_refresh)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(f"CurseForge file {file_identifier} is unavailable.")
        return CurseForgeClient._parse_file(data)

    @staticmethod
    def get_download_url(project_id: int | str, file_id: int | str, force_refresh: bool = False) -> str:
        project = CurseForgeClient._positive_int(project_id, "Project ID")
        file_identifier = CurseForgeClient._positive_int(file_id, "File ID")
        payload = CurseForgeClient._get_json(f"/mods/{project}/files/{file_identifier}/download-url", ttl=30 * 60, force_refresh=force_refresh)
        value = payload.get("data") if isinstance(payload, dict) else None
        return str(value or "").strip()

    @staticmethod
    def latest_compatible_file(project_id: int | str, game_version: str, release_types: tuple[str, ...] | list[str] | set[str] | None = None) -> CurseForgeFile:
        files = CurseForgeClient.list_files(project_id, game_version=game_version, release_types=release_types)
        if not files:
            raise RuntimeError(f"No Forge file for CurseForge project {project_id} supports Minecraft {game_version}.")
        return files[0]

    @staticmethod
    def normalize_release_types(release_types: tuple[str, ...] | list[str] | set[str] | None = None) -> tuple[str, ...]:
        if release_types is None:
            return ("release", "beta", "alpha")
        values = {str(item).strip().lower() for item in release_types if str(item).strip()}
        output = tuple(item for item in ("release", "beta", "alpha") if item in values)
        return output or ("release",)

    @staticmethod
    def _get_json(path: str, params: dict[str, object] | None = None, ttl: int = 0, force_refresh: bool = False) -> dict:
        api_key = CurseForgeClient.require_api_key()
        normalized_params = {str(key): value for key, value in (params or {}).items() if value not in {None, ""}}
        cache_key = hashlib.sha1(json.dumps([path, normalized_params], sort_keys=True, separators=(",", ":")).encode(), usedforsecurity=False).hexdigest()
        cache_path = Paths.curseforge_api_cache(cache_key)
        if not force_refresh:
            cached = CurseForgeClient._load_cache(cache_path, ttl)
            if cached is not None:
                return cached
        url = CurseForgeClient.BASE_URL + path
        try:
            response = HttpDownloader.get_client().get(url, params=normalized_params, headers={"Accept": "application/json", "User-Agent": CURSEFORGE_USER_AGENT, "x-api-key": api_key}, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as error:
            cached = CurseForgeClient._load_cache(cache_path, 0, ignore_expiry=True)
            if cached is not None:
                return cached
            if isinstance(error, httpx.HTTPStatusError) and error.response.status_code in {401, 403}:
                raise RuntimeError("CurseForge rejected the configured API key or the requested file is not available for third-party distribution.") from error
            raise RuntimeError(f"CurseForge request failed: {path}") from error
        if not isinstance(payload, dict):
            raise RuntimeError("CurseForge returned an invalid response.")
        CurseForgeClient._write_cache(cache_path, payload)
        return payload

    @staticmethod
    def _parse_project(data: dict) -> CurseForgeProject:
        authors = tuple(str(item.get("name") or "").strip() for item in data.get("authors", []) if isinstance(item, dict) and str(item.get("name") or "").strip())
        logo = data.get("logo") if isinstance(data.get("logo"), dict) else {}
        return CurseForgeProject(project_id=int(data.get("id", 0) or 0), name=str(data.get("name") or "Unknown project").strip(), slug=str(data.get("slug") or "").strip(), summary=str(data.get("summary") or "").strip(), download_count=int(data.get("downloadCount", 0) or 0), authors=authors, logo_url=str(logo.get("thumbnailUrl") or logo.get("url") or "").strip(), class_id=int(data.get("classId", 0) or 0), date_modified=str(data.get("dateModified") or "").strip())

    @staticmethod
    def _parse_file(data: dict) -> CurseForgeFile:
        hashes = data.get("hashes", []) if isinstance(data.get("hashes"), list) else []
        sha1 = ""
        for item in hashes:
            if isinstance(item, dict) and int(item.get("algo", 0) or 0) == 1:
                sha1 = str(item.get("value") or "").strip().lower()
                break
        dependencies = tuple(CurseForgeDependency(project_id=int(item.get("modId", 0) or 0), relation_type=int(item.get("relationType", 0) or 0)) for item in data.get("dependencies", []) if isinstance(item, dict) and int(item.get("modId", 0) or 0) > 0)
        release_type = {1: "release", 2: "beta", 3: "alpha"}.get(int(data.get("releaseType", 1) or 1), "release")
        return CurseForgeFile(file_id=int(data.get("id", 0) or 0), project_id=int(data.get("modId", 0) or 0), display_name=str(data.get("displayName") or data.get("fileName") or "Unknown file").strip(), file_name=Path(str(data.get("fileName") or "download.bin")).name, release_type=release_type, file_date=str(data.get("fileDate") or "").strip(), file_length=max(0, int(data.get("fileLength", 0) or 0)), download_url=str(data.get("downloadUrl") or "").strip(), sha1=sha1, game_versions=tuple(str(item) for item in data.get("gameVersions", []) if str(item).strip()), dependencies=dependencies, is_available=bool(data.get("isAvailable", True)))

    @staticmethod
    def _positive_int(value: int | str, label: str) -> int:
        try:
            result = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{label} must be a positive integer.") from error
        if result <= 0:
            raise ValueError(f"{label} must be a positive integer.")
        return result

    @staticmethod
    def _load_cache(path: Path, ttl: int, ignore_expiry: bool = False) -> dict | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            return None
        if not ignore_expiry and ttl > 0 and time() - float(payload.get("cachedAt", 0) or 0) > ttl:
            return None
        return payload["data"]

    @staticmethod
    def _write_cache(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps({"cachedAt": time(), "data": data}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
