from app.core.roles import ALL_ROLES
from app.core.supabase_client import (
    SupabaseError,
    admin_create_auth_user,
    eq,
    is_configured,
    rest_insert,
    rest_select,
    rest_update,
    sign_in_with_password,
)


PROFILE_COLUMNS = "*"


def authenticate_user(email: str, password: str) -> dict | None:
    if not is_configured():
        return None
    try:
        auth_response = sign_in_with_password(email.strip().lower(), password)
    except SupabaseError:
        return None

    auth_user = auth_response.get("user") or {}
    user_id = auth_user.get("id")
    if not user_id:
        return None

    profile = get_user_by_id(user_id)
    if not profile or not profile["is_active"]:
        return None
    profile["access_token"] = auth_response.get("access_token", "")
    return profile


def get_user_by_email(email: str) -> dict | None:
    rows = _profiles({"select": PROFILE_COLUMNS, "email": eq(email.strip().lower()), "limit": "1"})
    return public_user(rows[0]) if rows else None


def get_user_by_id(user_id: str) -> dict | None:
    rows = _profiles({"select": PROFILE_COLUMNS, "id": eq(str(user_id)), "limit": "1"})
    return public_user(rows[0]) if rows else None


def public_user(user: dict) -> dict:
    name = user.get("full_name") or user.get("name") or user["email"]
    return {
        "id": str(user["id"]),
        "name": name,
        "email": user["email"],
        "role": user["role"],
        "section": user.get("section") or "",
        "teacher_uid": user.get("teacher_uid") or "",
        "department": user.get("department") or "",
        "semester": user.get("semester") or "",
        "avatar_url": user.get("avatar_url") or "",
        "initials": _initials(name),
        "is_active": bool(user["is_active"]),
        "created_at": user.get("created_at", ""),
    }


def _initials(name: str) -> str:
    parts = [part for part in str(name or "").replace("@", " ").replace(".", " ").split() if part]
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def list_users(role: str = "") -> list[dict]:
    query = {
        "select": PROFILE_COLUMNS,
        "order": "role.asc,full_name.asc",
    }
    if role:
        query["role"] = eq(role)
    return [public_user(row) for row in _profiles(query)]


def user_counts_by_role() -> dict[str, int]:
    counts = {role: 0 for role in ALL_ROLES}
    for user in list_users():
        if user["is_active"]:
            counts[user["role"]] += 1
    return counts


def create_user(
    name: str,
    email: str,
    role: str,
    password: str,
) -> tuple[bool, str]:
    if role not in ALL_ROLES:
        return False, "Invalid role."
    if not name.strip() or not email.strip() or not password:
        return False, "Name, email, role, and password are required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not is_configured():
        return False, "Supabase is not configured."

    clean_email = email.strip().lower()
    clean_name = name.strip()
    try:
        auth_user = admin_create_auth_user(clean_email, password, clean_name, role)
        user_id = auth_user["id"]
        profile_payload = {
            "id": user_id,
            "full_name": clean_name,
            "email": clean_email,
            "role": role,
            "is_active": True,
        }
        rest_insert("profiles", profile_payload)
    except SupabaseError as exc:
        return False, str(exc)
    except KeyError:
        return False, "Supabase did not return the new Auth user id."
    return True, "User created successfully."


def set_user_active(user_id: str, is_active: bool) -> None:
    rest_update("profiles", {"id": eq(str(user_id))}, {"is_active": bool(is_active)})


def _profiles(query: dict[str, str]) -> list[dict]:
    if not is_configured():
        return []
    try:
        return rest_select("profiles", query)
    except SupabaseError:
        return []
