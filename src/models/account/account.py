from dataclasses import dataclass
from src.models.account.account_source import AccountSource
@dataclass(slots=True)
class Account:
    account_id:str
    account_type:AccountSource
    username:str
    uuid:str