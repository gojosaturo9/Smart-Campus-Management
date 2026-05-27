from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.auth.session import require_role
from app.core.analytics import admin_analytics_cards
from app.core.audit import audit_event
from app.core.roles import ADMIN, ALL_ROLES
from app.core.templates import templates
from app.core.users import (
    create_user,
    list_users,
    set_user_active,
    user_counts_by_role,
)

router = APIRouter(prefix="/admin")


@router.get("/analytics")
def analytics_page(
    request: Request,
    user=Depends(require_role(ADMIN)),
):
    return templates.TemplateResponse(
        "admin/analytics.html",
        {
            "request": request,
            "user": user,
            "analytics_cards": admin_analytics_cards(),
        },
    )


@router.get("/users")
def users_page(
    request: Request,
    role: str = "",
    created: str = "",
    error: str = "",
    user=Depends(require_role(ADMIN)),
):
    selected_role = role if role in ALL_ROLES else ""
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": user,
            "users": list_users(selected_role),
            "roles": ALL_ROLES,
            "selected_role": selected_role,
            "created": created,
            "error": error,
            "user_counts": user_counts_by_role(),
        },
    )


@router.post("/users")
def create_user_action(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    user=Depends(require_role(ADMIN)),
):
    ok, message = create_user(name, email, role, password)
    audit_event(
        "admin.user_create",
        user=user,
        request=request,
        target_email=email.strip().lower(),
        target_role=role,
        ok=ok,
        message=message,
    )
    flag = "created" if ok else "error"
    return RedirectResponse(f"/admin/users?{urlencode({flag: message})}", status_code=303)


@router.post("/users/{user_id}/status")
def set_user_status(
    request: Request,
    user_id: str,
    is_active: int = Form(...),
    user=Depends(require_role(ADMIN)),
):
    if user_id != user["id"]:
        set_user_active(user_id, bool(is_active))
        audit_event(
            "admin.user_status",
            user=user,
            request=request,
            target_user_id=user_id,
            is_active=bool(is_active),
        )
    return RedirectResponse("/admin/users", status_code=303)
