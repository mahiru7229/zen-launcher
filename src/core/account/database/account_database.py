import sqlite3

from src.core.fs.paths import Paths


class AccountDatabase:

    @staticmethod
    def initialize() -> None:
        database_path = Paths.account_database_path()
        database_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(database_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    account_type TEXT NOT NULL,
                    username TEXT NOT NULL,
                    uuid TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS account_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            connection.commit()