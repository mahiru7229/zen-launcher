from src.models.auth.authentication import Authentication
from src.models.account.account import Account
import hashlib
import uuid



class OfflineAuthentication:

    @staticmethod
    def authenticate(account:Account) -> Authentication:
        return Authentication(
            player_name=account.username,
            uuid=account.uuid,
            access_token="0",
            xuid="0",
            client_id="0",
            user_type="offline"
        )

    @staticmethod
    def uuid_generator(player_name:str) -> str:
        data = f"OfflinePlayer:{player_name}".encode("utf-8")

        md5 = bytearray(hashlib.md5(data).digest())

        # UUID version 3
        md5[6] &= 0x0F
        md5[6] |= 0x30

        # IETF variant
        md5[8] &= 0x3F
        md5[8] |= 0x80

        return str(uuid.UUID(bytes=bytes(md5)))




    