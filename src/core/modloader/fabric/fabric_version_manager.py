from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from threading import Lock
import json

import httpx

from src.core.fs.paths import Paths
from src.core.minecraft.version_manager import VersionManager
from src.core.modloader.fabric.fabric_meta_client import FabricMetaClient
from src.core.modloader.fabric.maven_artifact import MavenArtifact
from src.core.network.httpx_downloader import HttpDownloader
from src.core.progress.progress_reporter import ProgressReporter
from src.models.minecraft.version import Version
from src.models.progress.progress_stage import ProgressStage


class FabricVersionManager:
    _locks: dict[str, Lock] = {}
    _locks_guard = Lock()

    @staticmethod
    def load(game_version: str, loader_version: str, reporter: ProgressReporter | None = None) -> Version:
        base_version = VersionManager.load(game_version)
        return FabricVersionManager.install(base_version, loader_version, reporter)

    @staticmethod
    def recommended_loader_version(game_version: str) -> str:
        versions = FabricMetaClient.list_loader_versions(game_version)

        if not versions:
            raise RuntimeError(f"Fabric Loader is not available for Minecraft {game_version}.")

        recommended = next((version for version in versions if version.stable), versions[0])
        return recommended.version

    @staticmethod
    def install(base_version: Version, loader_version: str, reporter: ProgressReporter | None = None) -> Version:
        loader_version = loader_version.strip()
        if not loader_version:
            raise RuntimeError("Select a Fabric Loader version.")

        cache_path = Paths.fabric_version_json(base_version.id, loader_version)
        lock = FabricVersionManager._get_lock(f"{base_version.id}:{loader_version}")

        with lock:
            cached = FabricVersionManager._load_cached(cache_path, base_version.id, loader_version)
            if cached is not None:
                cached_version = VersionManager._parse_version(cached, cache_path)
                if cached_version is not None:
                    return cached_version

            if reporter is not None:
                reporter.status(stage=ProgressStage.INSTALLING_MOD_LOADER, message=f"Installing Fabric Loader {loader_version}...")

            profile = FabricMetaClient.get_profile(base_version.id, loader_version)
            normalized_profile = FabricVersionManager._normalize_profile_libraries(profile)
            merged = FabricVersionManager._merge_profiles(base_version.raw_json, normalized_profile, loader_version)
            FabricVersionManager._write_json(cache_path, merged)
            version = VersionManager._parse_version(merged, cache_path)

            if version is None:
                raise RuntimeError("Fabric version metadata could not be parsed.")
            return version

    @staticmethod
    def _get_lock(key: str) -> Lock:
        with FabricVersionManager._locks_guard:
            return FabricVersionManager._locks.setdefault(key, Lock())

    @staticmethod
    def _load_cached(path: Path, game_version: str, loader_version: str) -> dict | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

        fabric_data = data.get("fabric", {})
        if data.get("inheritsFrom") != game_version:
            return None
        if fabric_data.get("loaderVersion") != loader_version:
            return None
        if not data.get("mainClass") or not data.get("libraries"):
            return None
        return data

    @staticmethod
    def _normalize_profile_libraries(profile: dict) -> dict:
        normalized = deepcopy(profile)
        normalized_libraries: list[dict] = []

        for library in profile.get("libraries", []):
            if not isinstance(library, dict):
                continue

            item = deepcopy(library)
            artifact_data = item.get("downloads", {}).get("artifact")
            if artifact_data:
                normalized_libraries.append(item)
                continue

            coordinate = str(item.get("name", "")).strip()
            repository_url = str(item.get("url") or "https://maven.fabricmc.net/")
            artifact = MavenArtifact.from_coordinate(coordinate, repository_url)
            sha1, size = FabricVersionManager._load_artifact_metadata(artifact.url)
            item["downloads"] = {
                "artifact": {
                    "path": artifact.path.as_posix(),
                    "sha1": sha1,
                    "size": size,
                    "url": artifact.url,
                }
            }
            normalized_libraries.append(item)

        normalized["libraries"] = normalized_libraries
        return normalized

    @staticmethod
    def _load_artifact_metadata(url: str) -> tuple[str, int]:
        client = HttpDownloader.get_client()

        try:
            sha1_response = client.get(url + ".sha1", timeout=20.0)
            sha1_response.raise_for_status()
            sha1 = sha1_response.text.strip().split()[0].lower()
        except (httpx.HTTPError, IndexError) as error:
            raise RuntimeError(f"Unable to read Fabric library checksum: {url}") from error

        if len(sha1) != 40 or any(character not in "0123456789abcdef" for character in sha1):
            raise RuntimeError(f"Fabric library returned an invalid SHA-1 checksum: {url}")

        size = 0
        try:
            response = client.head(url, timeout=20.0)
            response.raise_for_status()
            size = int(response.headers.get("Content-Length", 0) or 0)
        except (httpx.HTTPError, ValueError):
            size = 0

        return sha1, size

    @staticmethod
    def _merge_profiles(base: dict, fabric: dict, loader_version: str) -> dict:
        merged = deepcopy(base)
        game_version = str(base["id"])
        profile_id = str(fabric.get("id") or f"fabric-loader-{loader_version}-{game_version}")

        merged["id"] = profile_id
        merged["inheritsFrom"] = game_version
        merged["mainClass"] = fabric["mainClass"]
        merged["type"] = fabric.get("type", base.get("type", "release"))
        merged["libraries"] = FabricVersionManager._merge_libraries(base.get("libraries", []), fabric.get("libraries", []))
        merged["arguments"] = FabricVersionManager._merge_arguments(base.get("arguments"), fabric.get("arguments"))

        base_legacy = str(base.get("minecraftArguments", "")).strip()
        fabric_legacy = str(fabric.get("minecraftArguments", "")).strip()
        if base_legacy or fabric_legacy:
            merged["minecraftArguments"] = " ".join(value for value in (base_legacy, fabric_legacy) if value)

        merged["fabric"] = {
            "loaderVersion": loader_version,
            "gameVersion": game_version,
            "profileId": profile_id,
        }
        return merged

    @staticmethod
    def _merge_libraries(base_libraries: list, fabric_libraries: list) -> list:
        merged: list[dict] = []
        indexes: dict[str, int] = {}

        for library in [*base_libraries, *fabric_libraries]:
            if not isinstance(library, dict):
                continue
            key = FabricVersionManager._library_key(str(library.get("name", "")))
            if key and key in indexes:
                merged[indexes[key]] = deepcopy(library)
                continue
            if key:
                indexes[key] = len(merged)
            merged.append(deepcopy(library))

        return merged

    @staticmethod
    def _library_key(coordinate: str) -> str:
        base_coordinate = coordinate.split("@", 1)[0]
        parts = base_coordinate.split(":")
        if len(parts) < 3:
            return coordinate
        group, artifact = parts[:2]
        classifier = parts[3] if len(parts) > 3 else ""
        return ":".join((group, artifact, classifier))

    @staticmethod
    def _merge_arguments(base_arguments: object, fabric_arguments: object) -> dict:
        base = deepcopy(base_arguments) if isinstance(base_arguments, dict) else {}
        fabric = fabric_arguments if isinstance(fabric_arguments, dict) else {}
        return {
            "jvm": [*base.get("jvm", []), *fabric.get("jvm", [])],
            "game": [*base.get("game", []), *fabric.get("game", [])],
        }

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".part")
        temp_path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(path)
