from dataclasses import dataclass



@dataclass(slots=True)
class MicrosoftConfig:
    client_id: str