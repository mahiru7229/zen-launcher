from dataclasses import dataclass

@dataclass(slots=True)
class Version:
    id: str
    arguments: dict
    libraries: list
    downloads: dict
    asset_index: dict
    assets: str
    main_class: str
    java_version: dict