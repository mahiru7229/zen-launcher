from dataclasses import dataclass




@dataclass
class DownloadAsset:
    logical_name: str 
    url: str
    sha1: str
    size: int