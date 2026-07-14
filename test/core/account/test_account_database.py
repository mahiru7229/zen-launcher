import sqlite3

from src.core.account.database.account_database import AccountDatabase
from src.core.fs.paths import Paths


def _use_temporary_database(monkeypatch, tmp_path):
    accounts_root = tmp_path / "accounts"
    monkeypatch.setattr(Paths, "ACCOUNTS_ROOT", accounts_root)
    return accounts_root / "accounts.db"


def test_initialize_creates_database_and_tables(monkeypatch, tmp_path) -> None:
    database_path = _use_temporary_database(monkeypatch, tmp_path)

    result = AccountDatabase.initialize()

    assert result == database_path
    assert database_path.is_file()

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]

    assert {"accounts", "account_state"}.issubset(tables)
    assert schema_version == AccountDatabase.SCHEMA_VERSION


def test_connect_repairs_an_empty_database(monkeypatch, tmp_path) -> None:
    database_path = _use_temporary_database(monkeypatch, tmp_path)
    database_path.parent.mkdir(parents=True)

    sqlite3.connect(database_path).close()

    with AccountDatabase.connect() as connection:
        account_count = connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]

    assert account_count == 0


def test_initialize_migrates_legacy_token_columns(monkeypatch, tmp_path) -> None:
    database_path = _use_temporary_database(monkeypatch, tmp_path)
    database_path.parent.mkdir(parents=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                account_type TEXT NOT NULL,
                username TEXT NOT NULL,
                uuid TEXT NOT NULL
            )
            """
        )

    AccountDatabase.initialize()

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(accounts)").fetchall()
        }

    assert {"access_token", "refresh_token", "token_expires_at"}.issubset(columns)
