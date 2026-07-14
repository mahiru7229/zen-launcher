from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FabricLoaderVersion:
    version: str
    stable: bool
