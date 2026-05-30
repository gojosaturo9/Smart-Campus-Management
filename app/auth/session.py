from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.core.roles import ALL_ROLES
from app.core.users import get_user_by_id, public_user


def set_login_session(request: Request, user: dict[str, Any]) -> None:
    request.session["user_id"] = user["id"]
    request.session["user"] = user


def clear_login_session(request: Request) -> None:
    request.session.clear()


def get_current_user(request: Request) -> dict[str, Any]:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    user = get_user_by_id(int(user_id))
    if not user or not user["is_active"]:
        clear_login_session(request)
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    user = public_user(user)
    request.session["user"] = user
    return user


def require_role(*allowed_roles: str):
    invalid_roles = set(allowed_roles) - set(ALL_ROLES)
    if invalid_roles:
        raise ValueError(f"Unknown role(s): {', '.join(sorted(invalid_roles))}")

    def dependency(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": f"/forbidden?needed={','.join(allowed_roles)}"},
            )
        return user

    return dependency
