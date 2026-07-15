from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MinecraftProfile:
    profile_id: str
    name: str
    skins: tuple[dict, ...] = ()
    capes: tuple[dict, ...] = ()

    @staticmethod
    def from_dict(data: dict) -> "MinecraftProfile":
        profile_id = str(data.get("id") or "").strip()
        name = str(data.get("name") or "").strip()
        if not profile_id or not name:
            raise ValueError("Minecraft profile response is incomplete.")
        skins = tuple(item for item in data.get("skins", []) if isinstance(item, dict))
        capes = tuple(item for item in data.get("capes", []) if isinstance(item, dict))
        return MinecraftProfile(profile_id=profile_id, name=name, skins=skins, capes=capes)
