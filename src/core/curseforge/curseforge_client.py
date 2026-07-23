from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock
from urllib.parse import quote
import json
import re

import httpx

from src.config import CURSEFORGE_USER_AGENT, VERSION_ID
from src.core.config.curseforge_config_manager import CurseForgeConfigManager
from src.core.curseforge.curseforge_cache import CacheLookup, CurseForgeCache
from src.core.network.httpx_downloader import HttpDownloader
from src.models.curseforge.cache import CurseForgeCacheInfo, CurseForgeFileListResult
from src.models.curseforge.file import CurseForgeDependency, CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult


@dataclass(slots=True)
class _InFlightRequest:
    event: Event
    result: CacheLookup | None = None
    error: Exception | None = None


class CurseForgeClient:
    MINECRAFT_GAME_ID = 432
    CLASS_MODS = 6
    CLASS_MODPACKS = 4471
    SEARCH_TTL_SECONDS = 30 * 60
    FILES_TTL_SECONDS = 60 * 60
    PROJECT_TTL_SECONDS = 12 * 60 * 60
    FILE_TTL_SECONDS = 24 * 60 * 60
    BATCH_TTL_SECONDS = 24 * 60 * 60
    REQUEST_TIMEOUT_SECONDS = 20.0

    _inflight: dict[str, _InFlightRequest] = {}
    _inflight_guard = Lock()

    @staticmethod
    def is_available() -> bool:
        return CurseForgeConfigManager.is_configured()

    @staticmethod
    def gateway_url() -> str:
        try:
            return CurseForgeConfigManager.gateway_url()
        except ValueError as error:
            raise RuntimeError(str(error)) from error

    @staticmethod
    def cache_status() -> CurseForgeCacheInfo:
        return CurseForgeCache.status()

    @staticmethod
    def clear_cache() -> None:
        CurseForgeCache.clear()

    @staticmethod
    def manual_refresh_remaining_seconds() -> int:
        return CurseForgeCache.manual_refresh_remaining_seconds()

    @staticmethod
    def search_projects(project_type: str, query: str = "", game_version: str = "", loader: str = "forge", index: int = 0, page_size: int = 25, sort: str = "popularity", force_refresh: bool = False, manual_refresh: bool = False) -> CurseForgeSearchResult:
        kind = str(project_type).strip().lower()
        if kind not in {"mod", "modpack"}:
            raise ValueError("CurseForge project type must be 'mod' or 'modpack'.")
        normalized_query = " ".join(str(query).strip().split())
        if not normalized_query:
            return CurseForgeSearchResult(
                projects=(),
                total_count=0,
                index=0,
                page_size=min(max(1, int(page_size)), 50),
                cache_info=CurseForgeCache.status(),
            )
        normalized_loader = CurseForgeClient.normalize_loader(loader)
        class_id = CurseForgeClient.CLASS_MODS if kind == "mod" else CurseForgeClient.CLASS_MODPACKS
        sort_field = {"popularity": 2, "updated": 3, "newest": 11, "downloads": 6}.get(str(sort).lower(), 2)
        params: dict[str, object] = {
            "query": normalized_query,
            "classId": class_id,
            "sortField": sort_field,
            "sortOrder": "desc",
            "index": max(0, int(index)),
            "pageSize": min(max(1, int(page_size)), 50),
        }
        if game_version:
            params["gameVersion"] = str(game_version).strip()
        if normalized_loader and game_version:
            params["loader"] = normalized_loader
        lookup = CurseForgeClient._request_json(
            "GET",
            "/search",
            params=params,
            ttl=CurseForgeClient.SEARCH_TTL_SECONDS,
            force_refresh=force_refresh,
            manual_refresh=manual_refresh,
            allow_stale_on_error=True,
            namespace="search",
        )
        payload = lookup.payload
        data = payload.get("data", []) if isinstance(payload, dict) else []
        pagination = payload.get("pagination", {}) if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict) else {}
        projects = tuple(CurseForgeClient._parse_project(item) for item in data if isinstance(item, dict))
        # CurseForge requires gameVersion when modLoaderType is used by the
        # project-search endpoint. Catalog mode intentionally has no game
        # version yet, so filter the current page using latestFilesIndexes.
        # Projects without index metadata remain visible to avoid false
        # negatives; their file list is still filtered by the files endpoint.
        if normalized_loader and not game_version:
            projects = tuple(
                project for project in projects
                if not project.loaders or normalized_loader in project.loaders
            )
        return CurseForgeSearchResult(
            projects=projects,
            total_count=int(pagination.get("totalCount", len(projects)) or 0),
            index=int(pagination.get("index", index) or 0),
            page_size=int(pagination.get("pageSize", page_size) or page_size),
            cache_info=lookup.cache_info,
        )

    @staticmethod
    def get_project(project_id: int | str, force_refresh: bool = False) -> CurseForgeProject:
        identifier = CurseForgeClient._positive_int(project_id, "Project ID")
        lookup = CurseForgeClient._request_json(
            "GET",
            "/mod",
            params={"modId": identifier},
            ttl=CurseForgeClient.PROJECT_TTL_SECONDS,
            force_refresh=force_refresh,
            allow_stale_on_error=True,
            namespace="project",
        )
        data = lookup.payload.get("data") if isinstance(lookup.payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(f"CurseForge project {identifier} is unavailable.")
        return CurseForgeClient._parse_project(data)

    @staticmethod
    def get_projects_batch(project_ids: list[int] | tuple[int, ...] | set[int]) -> dict[int, CurseForgeProject]:
        identifiers = CurseForgeClient._normalized_ids(project_ids, "Project ID")
        if not identifiers:
            return {}
        output: dict[int, CurseForgeProject] = {}
        for chunk in CurseForgeClient._chunks(identifiers, 50):
            lookup = CurseForgeClient._request_json(
                "POST",
                "/mods/batch",
                body={"modIds": list(chunk)},
                ttl=CurseForgeClient.BATCH_TTL_SECONDS,
                allow_stale_on_error=True,
                namespace="projects-batch",
            )
            data = lookup.payload.get("data", []) if isinstance(lookup.payload, dict) else []
            for item in data:
                if isinstance(item, dict):
                    project = CurseForgeClient._parse_project(item)
                    if project.project_id > 0:
                        output[project.project_id] = project
        return output

    @staticmethod
    def list_files_result(project_id: int | str, game_version: str = "", loader: str = "forge", release_types: tuple[str, ...] | list[str] | set[str] | None = None, page_size: int = 50, force_refresh: bool = False, manual_refresh: bool = False) -> CurseForgeFileListResult:
        identifier = CurseForgeClient._positive_int(project_id, "Project ID")
        normalized_loader = CurseForgeClient.normalize_loader(loader)
        params: dict[str, object] = {
            "modId": identifier,
            "pageSize": min(max(1, int(page_size)), 50),
            "index": 0,
        }
        if game_version:
            params["gameVersion"] = str(game_version).strip()
        # Unlike project search, CurseForge's files endpoint supports loader
        # filtering without requiring a Minecraft version. Catalog mode uses
        # this path before the user chooses or creates an instance.
        if normalized_loader:
            params["loader"] = normalized_loader
        lookup = CurseForgeClient._request_json(
            "GET",
            "/files",
            params=params,
            ttl=CurseForgeClient.FILES_TTL_SECONDS,
            force_refresh=force_refresh,
            manual_refresh=manual_refresh,
            allow_stale_on_error=True,
            namespace="files",
        )
        data = lookup.payload.get("data", []) if isinstance(lookup.payload, dict) else []
        allowed = set(CurseForgeClient.normalize_release_types(release_types))
        files = [CurseForgeClient._parse_file(item) for item in data if isinstance(item, dict)]
        files = [item for item in files if item.release_type in allowed]
        if normalized_loader:
            files = [item for item in files if not item.loaders or normalized_loader in item.loaders]
        files.sort(key=lambda item: item.file_date, reverse=True)
        return CurseForgeFileListResult(files=tuple(files), cache_info=lookup.cache_info)

    @staticmethod
    def list_files(project_id: int | str, game_version: str = "", loader: str = "forge", release_types: tuple[str, ...] | list[str] | set[str] | None = None, page_size: int = 50, force_refresh: bool = False) -> list[CurseForgeFile]:
        result = CurseForgeClient.list_files_result(
            project_id,
            game_version=game_version,
            loader=loader,
            release_types=release_types,
            page_size=page_size,
            force_refresh=force_refresh,
        )
        return list(result.files)

    @staticmethod
    def get_file(project_id: int | str, file_id: int | str, force_refresh: bool = False) -> CurseForgeFile:
        project = CurseForgeClient._positive_int(project_id, "Project ID")
        file_identifier = CurseForgeClient._positive_int(file_id, "File ID")
        lookup = CurseForgeClient._request_json(
            "GET",
            "/file",
            params={"modId": project, "fileId": file_identifier},
            ttl=CurseForgeClient.FILE_TTL_SECONDS,
            force_refresh=force_refresh,
            allow_stale_on_error=True,
            namespace="file",
        )
        data = lookup.payload.get("data") if isinstance(lookup.payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(f"CurseForge file {file_identifier} is unavailable.")
        return CurseForgeClient._parse_file(data)

    @staticmethod
    def get_files_batch(file_ids: list[int] | tuple[int, ...] | set[int]) -> dict[int, CurseForgeFile]:
        identifiers = CurseForgeClient._normalized_ids(file_ids, "File ID")
        if not identifiers:
            return {}
        output: dict[int, CurseForgeFile] = {}
        for chunk in CurseForgeClient._chunks(identifiers, 50):
            lookup = CurseForgeClient._request_json(
                "POST",
                "/files/batch",
                body={"fileIds": list(chunk)},
                ttl=CurseForgeClient.BATCH_TTL_SECONDS,
                allow_stale_on_error=True,
                namespace="files-batch",
            )
            data = lookup.payload.get("data", []) if isinstance(lookup.payload, dict) else []
            for item in data:
                if isinstance(item, dict):
                    file = CurseForgeClient._parse_file(item)
                    if file.file_id > 0:
                        output[file.file_id] = file
        return output

    @staticmethod
    def get_download_url(project_id: int | str, file_id: int | str, force_refresh: bool = False) -> str:
        project = CurseForgeClient._positive_int(project_id, "Project ID")
        file_identifier = CurseForgeClient._positive_int(file_id, "File ID")
        lookup = CurseForgeClient._request_json(
            "GET",
            "/download-url",
            params={"modId": project, "fileId": file_identifier},
            ttl=0,
            force_refresh=force_refresh,
            allow_stale_on_error=False,
            cache_response=False,
            namespace="download-url",
        )
        value = lookup.payload.get("data") if isinstance(lookup.payload, dict) else None
        return str(value or "").strip()

    @staticmethod
    def latest_compatible_file(project_id: int | str, game_version: str, loader: str = "forge", release_types: tuple[str, ...] | list[str] | set[str] | None = None) -> CurseForgeFile:
        files = CurseForgeClient.list_files(project_id, game_version=game_version, loader=loader, release_types=release_types)
        if not files:
            raise RuntimeError(f"No {loader.title()} file for CurseForge project {project_id} supports Minecraft {game_version}.")
        return files[0]

    @staticmethod
    def normalize_loader(loader: str) -> str:
        normalized = str(loader).strip().casefold()
        if normalized in {"forge", "fabric", "quilt", "neoforge"}:
            return normalized
        return ""

    @staticmethod
    def normalize_release_types(release_types: tuple[str, ...] | list[str] | set[str] | None = None) -> tuple[str, ...]:
        if release_types is None:
            return ("release", "beta", "alpha")
        values = {str(item).strip().lower() for item in release_types if str(item).strip()}
        output = tuple(item for item in ("release", "beta", "alpha") if item in values)
        return output or ("release",)

    @staticmethod
    def _request_json(method: str, route: str, params: dict[str, object] | None = None, body: object | None = None, ttl: int = 0, force_refresh: bool = False, manual_refresh: bool = False, allow_stale_on_error: bool = True, cache_response: bool = True, namespace: str = "generic") -> CacheLookup:
        normalized_params = {str(key): value for key, value in (params or {}).items() if value not in {None, ""}}
        cache_key = CurseForgeCache.make_key(namespace, route, normalized_params, body)
        if cache_response and not force_refresh:
            cached = CurseForgeCache.get(cache_key, ttl, allow_stale=False)
            if cached is not None:
                return cached
        if manual_refresh:
            CurseForgeCache.assert_manual_refresh_allowed()

        with CurseForgeClient._inflight_guard:
            in_flight = CurseForgeClient._inflight.get(cache_key)
            if in_flight is None:
                in_flight = _InFlightRequest(event=Event())
                CurseForgeClient._inflight[cache_key] = in_flight
                owner = True
            else:
                owner = False
        if not owner:
            if not in_flight.event.wait(CurseForgeClient.REQUEST_TIMEOUT_SECONDS + 10):
                raise RuntimeError("Timed out while waiting for an identical CurseForge request.")
            if in_flight.error is not None:
                raise in_flight.error
            if in_flight.result is None:
                raise RuntimeError("The shared CurseForge request completed without a result.")
            return in_flight.result

        try:
            CurseForgeCache.record_attempt(manual=manual_refresh)
            lookup = CurseForgeClient._perform_request(method, route, normalized_params, body, ttl, cache_key, namespace, cache_response)
            in_flight.result = lookup
            return lookup
        except Exception as error:
            retry_after = int(getattr(error, "retry_after_seconds", 0) or 0) or None
            CurseForgeCache.record_failure(str(error), retry_after_seconds=retry_after)
            if allow_stale_on_error and cache_response:
                stale = CurseForgeCache.get(cache_key, ttl, allow_stale=True)
                if stale is not None:
                    in_flight.result = stale
                    return stale
            in_flight.error = error
            raise
        finally:
            in_flight.event.set()
            with CurseForgeClient._inflight_guard:
                CurseForgeClient._inflight.pop(cache_key, None)

    @staticmethod
    def _perform_request(method: str, route: str, params: dict[str, object], body: object | None, ttl: int, cache_key: str, namespace: str, cache_response: bool) -> CacheLookup:
        headers = {
            "Accept": "application/json",
            "User-Agent": CURSEFORGE_USER_AGENT,
            "X-MCW-Version": VERSION_ID,
        }
        token = CurseForgeConfigManager.client_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = CurseForgeClient.gateway_url() + route
        client = HttpDownloader.get_client()
        try:
            response = client.request(
                method.upper(),
                url,
                params=params or None,
                json=body if method.upper() != "GET" else None,
                headers=headers,
                timeout=CurseForgeClient.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as error:
            raise CurseForgeClient._gateway_error(error.response) from error
        except httpx.HTTPError as error:
            raise RuntimeError(f"Unable to contact the CurseForge gateway: {error}") from error
        except ValueError as error:
            raise RuntimeError("The CurseForge gateway returned invalid JSON.") from error
        if not isinstance(payload, dict):
            raise RuntimeError("The CurseForge gateway returned an invalid response.")
        if cache_response:
            return CurseForgeCache.put(cache_key, namespace, payload, ttl)
        return CacheLookup(payload=payload, cache_info=CurseForgeCache.status())

    @staticmethod
    def _gateway_error(response: httpx.Response) -> RuntimeError:
        status = int(response.status_code)
        code = ""
        message = ""
        request_id = str(response.headers.get("x-request-id") or "").strip()
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            code = str(payload["error"].get("code") or "").strip()
            message = str(payload["error"].get("message") or "").strip()
            request_id = str(payload["error"].get("requestId") or request_id).strip()
        if not message:
            message = f"CurseForge gateway request failed with HTTP {status}."
        if request_id:
            message += f" Request ID: {request_id}."
        error = RuntimeError(message)
        setattr(error, "gateway_status", status)
        retry_after = response.headers.get("retry-after")
        try:
            setattr(error, "retry_after_seconds", max(0, int(retry_after or 0)))
        except ValueError:
            setattr(error, "retry_after_seconds", 0)
        setattr(error, "gateway_error_code", code)
        return error

    @staticmethod
    def _parse_project(data: dict) -> CurseForgeProject:
        authors = tuple(str(item.get("name") or "").strip() for item in data.get("authors", []) if isinstance(item, dict) and str(item.get("name") or "").strip())
        logo = data.get("logo") if isinstance(data.get("logo"), dict) else {}
        links = data.get("links") if isinstance(data.get("links"), dict) else {}
        project_id = int(data.get("id", 0) or 0)
        slug = str(data.get("slug") or "").strip()
        project_url = str(links.get("websiteUrl") or "").strip()
        loader_names = {0: "any", 1: "forge", 2: "cauldron", 3: "liteloader", 4: "fabric", 5: "quilt", 6: "neoforge"}
        indexes = data.get("latestFilesIndexes", []) if isinstance(data.get("latestFilesIndexes"), list) else []
        game_versions = tuple(dict.fromkeys(
            str(item.get("gameVersion") or "").strip()
            for item in indexes
            if isinstance(item, dict) and CurseForgeClient._is_minecraft_version(str(item.get("gameVersion") or ""))
        ))
        loaders = tuple(dict.fromkeys(
            loader_names.get(int(item.get("modLoader", -1) or -1), "")
            for item in indexes
            if isinstance(item, dict) and loader_names.get(int(item.get("modLoader", -1) or -1), "") not in {"", "any"}
        ))
        if not project_url and slug:
            project_url = f"https://www.curseforge.com/minecraft/mc-mods/{quote(slug, safe='-')}"
        return CurseForgeProject(
            project_id=project_id,
            name=str(data.get("name") or "Unknown project").strip(),
            slug=slug,
            summary=str(data.get("summary") or "").strip(),
            download_count=int(data.get("downloadCount", 0) or 0),
            authors=authors,
            logo_url=str(logo.get("thumbnailUrl") or logo.get("url") or "").strip(),
            class_id=int(data.get("classId", 0) or 0),
            date_modified=str(data.get("dateModified") or "").strip(),
            project_url=project_url,
            game_versions=game_versions,
            loaders=loaders,
        )

    @staticmethod
    def _parse_file(data: dict) -> CurseForgeFile:
        hashes = data.get("hashes", []) if isinstance(data.get("hashes"), list) else []
        sha1 = ""
        for item in hashes:
            if isinstance(item, dict) and int(item.get("algo", 0) or 0) == 1:
                sha1 = str(item.get("value") or "").strip().lower()
                break
        dependencies = tuple(
            CurseForgeDependency(
                project_id=int(item.get("modId", 0) or 0),
                relation_type=int(item.get("relationType", 0) or 0),
            )
            for item in data.get("dependencies", [])
            if isinstance(item, dict) and int(item.get("modId", 0) or 0) > 0
        )
        release_type = {1: "release", 2: "beta", 3: "alpha"}.get(int(data.get("releaseType", 1) or 1), "release")
        raw_versions = tuple(str(item).strip() for item in data.get("gameVersions", []) if str(item).strip())
        known_loaders = {"forge", "fabric", "quilt", "neoforge"}
        loaders = tuple(dict.fromkeys(value.casefold() for value in raw_versions if value.casefold() in known_loaders))
        game_versions = tuple(value for value in raw_versions if CurseForgeClient._is_minecraft_version(value))
        return CurseForgeFile(
            file_id=int(data.get("id", 0) or 0),
            project_id=int(data.get("modId", 0) or 0),
            display_name=str(data.get("displayName") or data.get("fileName") or "Unknown file").strip(),
            file_name=Path(str(data.get("fileName") or "download.bin")).name,
            release_type=release_type,
            file_date=str(data.get("fileDate") or "").strip(),
            file_length=max(0, int(data.get("fileLength", 0) or 0)),
            download_url=str(data.get("downloadUrl") or "").strip(),
            sha1=sha1,
            game_versions=game_versions,
            dependencies=dependencies,
            is_available=bool(data.get("isAvailable", True)),
            loaders=loaders,
        )

    @staticmethod
    def _is_minecraft_version(value: str) -> bool:
        normalized = str(value).strip().casefold()
        return bool(
            re.fullmatch(r"\d+\.\d+(?:\.\d+)?(?:[-+._a-z0-9]*)?", normalized)
            or re.fullmatch(r"\d{2}w\d{2}[a-z]", normalized)
        )

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
    def _normalized_ids(values: list[int] | tuple[int, ...] | set[int], label: str) -> tuple[int, ...]:
        output: list[int] = []
        seen: set[int] = set()
        for value in values:
            identifier = CurseForgeClient._positive_int(value, label)
            if identifier not in seen:
                seen.add(identifier)
                output.append(identifier)
        return tuple(output)

    @staticmethod
    def _chunks(values: tuple[int, ...], size: int) -> tuple[tuple[int, ...], ...]:
        return tuple(values[index:index + size] for index in range(0, len(values), size))
