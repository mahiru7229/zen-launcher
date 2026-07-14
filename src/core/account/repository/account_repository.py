import sqlite3

from src.core.account.database.account_database import AccountDatabase
from src.core.security.token_cipher import TokenCipher
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


class AccountRepository:
    SELECTED_ACCOUNT_KEY = "selected_account_id"

    @staticmethod
    def save(account: Account) -> None:
        access_token = TokenCipher.encrypt(account.access_token) if account.access_token else None
        refresh_token = TokenCipher.encrypt(account.refresh_token) if account.refresh_token else None

        with AccountDatabase.connect() as connection:
            connection.execute(
                """
                INSERT INTO accounts (
                    account_id,
                    account_type,
                    username,
                    uuid,
                    access_token,
                    refresh_token,
                    token_expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    account_type = excluded.account_type,
                    username = excluded.username,
                    uuid = excluded.uuid,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    token_expires_at = excluded.token_expires_at
                """,
                (
                    account.account_id,
                    account.account_type.value,
                    account.username,
                    account.uuid,
                    access_token,
                    refresh_token,
                    account.token_expires_at,
                ),
            )

    @staticmethod
    def get(account_id: str) -> Account | None:
        with AccountDatabase.connect() as connection:
            row = connection.execute(
                """
                SELECT account_id, account_type, username, uuid, access_token, refresh_token, token_expires_at
                FROM accounts
                WHERE account_id = ?
                """,
                (account_id,),
            ).fetchone()

        if row is None:
            return None

        return AccountRepository._row_to_account(row)

    @staticmethod
    def list_accounts() -> list[Account]:
        with AccountDatabase.connect() as connection:
            rows = connection.execute(
                """
                SELECT account_id, account_type, username, uuid, access_token, refresh_token, token_expires_at
                FROM accounts
                ORDER BY username COLLATE NOCASE ASC
                """
            ).fetchall()

        return [AccountRepository._row_to_account(row) for row in rows]

    @staticmethod
    def remove(account_id: str) -> bool:
        with AccountDatabase.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM accounts WHERE account_id = ?",
                (account_id,),
            )

            if cursor.rowcount > 0:
                connection.execute(
                    "DELETE FROM account_state WHERE key = ? AND value = ?",
                    (AccountRepository.SELECTED_ACCOUNT_KEY, account_id),
                )

            return cursor.rowcount > 0

    @staticmethod
    def set_selected_account(account_id: str) -> bool:
        if AccountRepository.get(account_id) is None:
            return False

        with AccountDatabase.connect() as connection:
            connection.execute(
                """
                INSERT INTO account_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value
                """,
                (AccountRepository.SELECTED_ACCOUNT_KEY, account_id),
            )

        return True

    @staticmethod
    def get_selected_account() -> Account | None:
        with AccountDatabase.connect() as connection:
            row = connection.execute(
                "SELECT value FROM account_state WHERE key = ?",
                (AccountRepository.SELECTED_ACCOUNT_KEY,),
            ).fetchone()

        if row is None:
            return None

        return AccountRepository.get(row["value"])

    @staticmethod
    def _row_to_account(row: sqlite3.Row) -> Account:
        access_token = TokenCipher.decrypt(row["access_token"]) if row["access_token"] else None
        refresh_token = TokenCipher.decrypt(row["refresh_token"]) if row["refresh_token"] else None

        return Account(
            account_id=row["account_id"],
            account_type=AccountSource(row["account_type"]),
            username=row["username"],
            uuid=row["uuid"],
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=row["token_expires_at"],
        )
