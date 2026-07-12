from src.models.minecraft.version import Version
from pathlib import Path
from dataclasses import dataclass


@dataclass(slots=True)
class Instance:
    instance_id: str
    name:str
    version_id: str
    instance_dir: Path
    mod_loader: tuple #fabric, forge, vanilla, ... ex = ("fabric", "0.19.1")