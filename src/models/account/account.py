from dataclasses import dataclass


@dataclass(slots=True)
class Account:
    account_id:str
    account_type:str
    username:str
    uuid:str