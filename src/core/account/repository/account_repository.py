import sqlite3

from src.core.fs.paths import Paths
from src.models.account.account import Account
from src.models.account.account_source import AccountSource


class AccountRepository:

    @staticmethod
    def save(account: Account) -> None:
        database_path = Paths.account_database_path()

        with sqlite3.connect(database_path) as connection:
            connection.execute("""
                INSERT INTO accounts (
                    account_id,
                    account_type,
                    username,
                    uuid
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    account_type = excluded.account_type,
                    username = excluded.username,
                    uuid = excluded.uuid
            """, (
                account.account_id,
                account.account_type.value,
                account.username,
                account.uuid
            ))

            connection.commit()

    @staticmethod
    def get(account_id: str) -> Account | None:
        database_path = Paths.account_database_path()

        with sqlite3.connect(database_path) as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute("""
                SELECT account_id, account_type, username, uuid
                FROM accounts
                WHERE account_id = ?
            """, (account_id,)).fetchone()

        if row is None:
            return None

        return AccountRepository._row_to_account(row)

    @staticmethod
    def list_accounts() -> list[Account]:
        database_path = Paths.account_database_path()

        with sqlite3.connect(database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute("""
                SELECT account_id, account_type, username, uuid
                FROM accounts
                ORDER BY username ASC
            """).fetchall()

        return [
            AccountRepository._row_to_account(row)
            for row in rows
        ]


    @staticmethod
    def remove(account_id: str) -> bool:
        database_path = Paths.account_database_path()

        with sqlite3.connect(database_path) as connection:
            cursor = connection.execute("""
                DELETE FROM accounts
                WHERE account_id = ?
            """, (account_id,))

            if cursor.rowcount > 0:
                connection.execute("""
                    DELETE FROM account_state
                    WHERE key = ?
                    AND value = ?
                """, (
                    "selected_account_id",
                    account_id
                ))

            connection.commit()

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_account(row: sqlite3.Row) -> Account:
        return Account(
            account_id=row["account_id"],
            account_type=AccountSource(row["account_type"]),
            username=row["username"],
            uuid=row["uuid"]
        )
    
    def set_selected_account(account_id: str) -> bool:
        account = AccountRepository.get(account_id)

        if account is None:
            return False

        database_path = Paths.account_database_path()

        with sqlite3.connect(database_path) as connection:
            connection.execute("""
                INSERT INTO account_state (
                    key,
                    value
                )
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value
            """, (
                "selected_account_id",
                account_id
            ))

            connection.commit()

        return True

    @staticmethod
    def get_selected_account() -> Account | None:
        database_path = Paths.account_database_path()

        with sqlite3.connect(database_path) as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute("""
                SELECT value
                FROM account_state
                WHERE key = ?
            """, ("selected_account_id",)).fetchone()

        if row is None:
            return None

        return AccountRepository.get(row["value"])