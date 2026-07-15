import uuid

from src.core.auth.offline_auth import OfflineAuthentication
from src.core.account.repository.account_repository import AccountRepository
from src.models.account.account import Account
from src.models.account.account_source import AccountSource
from src.core.auth.microsoft.microsoft_account_authenticator import MicrosoftAccountAuthenticator


class AccountManager:

    @staticmethod
    def create_offline_account(username: str) -> Account:
        if not username.strip():
            raise ValueError("Username cannot be empty.")

        if AccountManager.is_account_exist(username):
            raise RuntimeError(
                f"Account '{username}' already exists."
            )

        account = Account(
            account_id=str(uuid.uuid4()),
            account_type=AccountSource.OFFLINE,
            username=username,
            uuid=OfflineAuthentication.uuid_generator(username)
        )

        AccountRepository.save(account)

        if AccountRepository.get_selected_account() is None:
            AccountRepository.set_selected_account(account.account_id)

        return account

    @staticmethod
    def create_microsoft_account() -> Account:
        account = MicrosoftAccountAuthenticator.authenticate()
        if AccountManager.is_account_exist(account.username):
            raise RuntimeError(f"Account '{account.username}' already exists.")
        AccountRepository.save(account)
        AccountRepository.set_selected_account(account.account_id)
        return account

    @staticmethod
    def list_accounts() -> list[Account]:
        return AccountRepository.list_accounts()

    @staticmethod
    def get_account(account_id: str) -> Account | None:
        return AccountRepository.get(account_id)

    @staticmethod
    def get_selected_account() -> Account | None:
        selected_account = AccountRepository.get_selected_account()

        if selected_account is not None:
            return selected_account

        accounts = AccountRepository.list_accounts()

        if not accounts:
            return None

        first_account = accounts[0]
        AccountRepository.set_selected_account(first_account.account_id)

        return first_account

    @staticmethod
    def set_selected_account(account_id: str) -> bool:
        return AccountRepository.set_selected_account(account_id)

    @staticmethod
    def remove_account(account_id: str) -> bool:
        selected_account = AccountRepository.get_selected_account()

        removed = AccountRepository.remove(account_id)

        if not removed:
            return False

        if selected_account is None:
            return True

        if selected_account.account_id != account_id:
            return True

        remaining_accounts = AccountRepository.list_accounts()

        if remaining_accounts:
            AccountRepository.set_selected_account(
                remaining_accounts[0].account_id
            )

        return True

    @staticmethod
    def is_account_exist(username: str) -> bool:
        normalized_username = username.casefold()

        for account in AccountRepository.list_accounts():
            if account.username.casefold() == normalized_username:
                return True

        return False