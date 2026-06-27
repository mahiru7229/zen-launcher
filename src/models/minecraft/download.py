from dataclasses import dataclass


@dataclass(slots=True)
class DownloadClient:
    url:str
    sha1:str
    size:int