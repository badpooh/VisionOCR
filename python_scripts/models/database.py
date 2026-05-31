import sqlite3
import os


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "settings.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with _connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " type TEXT NOT NULL UNIQUE,"
            " value TEXT NOT NULL"
            ")"
        )
    print("Database and table have been initialized.")


def save_or_update_setting(key: str, value: str):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO settings (type, value) VALUES (?, ?)"
            " ON CONFLICT(type) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def load_setting(key: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE type = ?", (key,)
        ).fetchone()
        return row[0] if row else None