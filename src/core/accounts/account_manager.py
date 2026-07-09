from src.core.fs.paths import Paths
from src.core.auth.offline_auth import OfflineAuthentication
from src.models.account.account import Account
import json
import uuid



# format
# {
#     "selected_account_id": "",
#     "accounts": []
# }




class AccountManager:
    @staticmethod
    def load_accounts() -> dict:
        try:
            return json.loads(Paths.accounts_path().read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = AccountManager.default_accounts_data()
            AccountManager.save_accounts(data)
            return data
    
    @staticmethod
    def default_accounts_data() -> dict:
        return {
            "selected_account_id": "",
            "accounts": []
        }

    
    @staticmethod
    def save_accounts(data:dict) -> None:
        path = Paths.accounts_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data,indent=4, ensure_ascii=False), encoding="utf-8")




    @staticmethod
    def create_offline_account(username: str) -> Account:
        data = AccountManager.load_accounts()
        data.setdefault("accounts", [])
        if AccountManager.is_account_exist(username):
            raise RuntimeError(
                f"Account '{username}' already exists."
            )
        account = Account(
            account_id=str(uuid.uuid4()),
            account_type="offline",
            username=username,
            uuid=OfflineAuthentication.uuid_generator(username)
        )

        data["accounts"].append({
            "account_id": account.account_id,
            "account_type": account.account_type,
            "username": account.username,
            "uuid": account.uuid
        })
        AccountManager._ensure_selected_account(data)
        AccountManager.save_accounts(data)
        return account


    @staticmethod
    def set_selected_account(account_id:str) -> bool:
        data = AccountManager.load_accounts()
        for account_data in data.get("accounts", []):
            account = AccountManager._parse_account(account_data)
            if account is None:
                continue
            if account.account_id == account_id:
                data["selected_account_id"] = account_id
                AccountManager.save_accounts(data)
                return True
        return False

    @staticmethod
    def _ensure_selected_account(data: dict) -> None:
        accounts = data.get("accounts", [])

        if not accounts:
            data["selected_account_id"] = ""
            return

        selected_id = data.get("selected_account_id")

        for account_data in accounts:
            if account_data.get("account_id") == selected_id:
                return

        data["selected_account_id"] = accounts[0].get("account_id", "")

    @staticmethod
    def get_selected_account() -> Account | None:
        data = AccountManager.load_accounts()
        selected_id = data.get("selected_account_id")
        if not selected_id:
            return None
        for account_data in data.get("accounts", []):
            account = AccountManager._parse_account(account_data)
            if account is None:
                continue
            if account.account_id == selected_id:
                return account

        return None

    @staticmethod
    def _parse_account(data:dict) -> Account | None:
        account_id = data.get("account_id")
        account_type = data.get("account_type")
        username = data.get("username")
        user_uuid = data.get("uuid")

        if not all([account_id, account_type,username, user_uuid]):
            return None


        return Account(
            account_id=account_id,
            account_type=account_type,
            username=username,
            uuid=user_uuid
        )


    @staticmethod
    def list_accounts() -> list[Account]:
        data = AccountManager.load_accounts()
        accounts:list[Account]  = []
        for account_data in data.get("accounts", []):
            account = AccountManager._parse_account(account_data)
            if account is None:
                continue
            accounts.append(account)
        return accounts
    
    @staticmethod
    def remove_account(account_id:str) -> bool:
        data = AccountManager.load_accounts()
        old_accounts_data:list[dict] = data.get("accounts", [])
        new_accounts_data:list[dict] = []
        for account_data in old_accounts_data:
            if account_data.get("account_id") == account_id:
                if account_id == data.get("selected_account_id"):
                    data["selected_account_id"]=""
                continue
            new_accounts_data.append(account_data)
        if len(old_accounts_data) == len(new_accounts_data):
            return False # not found
        data["accounts"] = new_accounts_data
        AccountManager._ensure_selected_account(data)
        AccountManager.save_accounts(data)
        return True
    

    @staticmethod
    def is_account_exist(username: str) -> bool:
        data = AccountManager.load_accounts()
        for account_data in data.get("accounts", []):
            account = AccountManager._parse_account(account_data)
            if account is None:
                continue
            if account.username == username:
                return True
        return False