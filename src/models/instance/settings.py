from pathlib import Path
from dataclasses import dataclass, field



@dataclass
class InstanceSettings:
    java_path: Path
    min_memory: int = 1024
    max_memory: int = 2048

    jvm_arguments: list[str] = field(default_factory=list)
    game_arguments: list[str] = field(default_factory=list)

    width: int = 854
    height: int = 480
    fullscreen: bool = False