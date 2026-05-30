from datetime import datetime, timezone
from sqlite3 import IntegrityError

from app.core.db import get_connection
from app.core.roles import ALL_ROLES
from app.core.security import hash_password, verify_password


def authenticate_user(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if not user or not user["is_active"]:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return public_user(user)


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE lower(email) = lower(?)",
            (email.strip(),),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "is_active": bool(user["is_active"]),
    }


def list_users(role: str = "") -> list[dict]:
    query = "SELECT id, name, email, role, is_active, created_at FROM users"
    params: tuple = ()
    if role:
        query += " WHERE role = ?"
        params = (role,)
    query += " ORDER BY role, name"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def user_counts_by_role() -> dict[str, int]:
    counts = {role: 0 for role in ALL_ROLES}
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT role, COUNT(*) AS total FROM users WHERE is_active = 1 GROUP BY role"
        ).fetchall()
    for row in rows:
        counts[row["role"]] = row["total"]
    return counts


def create_user(name: str, email: str, role: str, password: str) -> tuple[bool, str]:
    if role not in ALL_ROLES:
        return False, "Invalid role."
    if not name.strip() or not email.strip() or not password:
        return False, "Name, email, role, and password are required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    now = datetime.now(timezone.utc).isoformat()
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (name, email, role, password_hash, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (name.strip(), email.strip().lower(), role, hash_password(password), now),
            )
    except IntegrityError:
        return False, "A user with this email already exists."
    return True, "User created successfully."


def set_user_active(user_id: int, is_active: bool) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, user_id),
        )
