import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.core.roles import ADMIN, ALUMNI, STUDENT, TEACHER
from app.core.security import hash_password


def get_connection() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
            """
        )
        _seed_users(connection)


def _seed_users(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return

    now = datetime.now(timezone.utc).isoformat()
    users: Iterable[tuple[str, str, str, str, int, str]] = (
        ("Platform Admin", "admin@campus.local", ADMIN, hash_password("Admin@123"), 1, now),
        ("Student Demo", "student@campus.local", STUDENT, hash_password("Student@123"), 1, now),
        ("Teacher Demo", "teacher@campus.local", TEACHER, hash_password("Teacher@123"), 1, now),
        ("Alumni Demo", "alumni@campus.local", ALUMNI, hash_password("Alumni@123"), 1, now),
    )
    connection.executemany(
        """
        INSERT INTO users (name, email, role, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        users,
    )


def database_exists() -> bool:
    return Path(settings.database_path).exists()
