from __future__ import annotations

import httpx

from src.core.network.httpx_downloader import HttpDownloader
from src.models.modloader.fabric_loader_version import FabricLoaderVersion


class FabricMetaClient:
    BASE_URL = "https://meta.fabricmc.net/v2"

    @staticmethod
    def list_loader_versions(game_version: str) -> list[FabricLoaderVersion]:
        data = FabricMetaClient._get_json(f"/versions/loader/{game_version}")
        versions: list[FabricLoaderVersion] = []

        if not isinstance(data, list):
            raise RuntimeError("Fabric Meta returned an invalid loader list.")

        for item in data:
            if not isinstance(item, dict):
                continue
            loader = item.get("loader", item)
            version = str(loader.get("version", "")).strip() if isinstance(loader, dict) else ""
            if not version:
                continue
            stable = bool(loader.get("stable", item.get("stable", False))) if isinstance(loader, dict) else False
            versions.append(FabricLoaderVersion(version=version, stable=stable))

        return versions

    @staticmethod
    def get_profile(game_version: str, loader_version: str) -> dict:
        data = FabricMetaClient._get_json(f"/versions/loader/{game_version}/{loader_version}/profile/json")
        if not isinstance(data, dict) or not data.get("mainClass"):
            raise RuntimeError(f"Fabric profile is unavailable for Minecraft {game_version} and loader {loader_version}.")
        return data

    @staticmethod
    def _get_json(path: str) -> object:
        client = HttpDownloader.get_client()
        try:
            response = client.get(FabricMetaClient.BASE_URL + path, timeout=20.0)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise RuntimeError("Unable to contact Fabric Meta.") from error
