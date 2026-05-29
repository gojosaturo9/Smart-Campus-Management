from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.auth.session import require_role
from app.core.alumni_mentorship import delete_notification
from app.core.roles import ALUMNI, STUDENT

router = APIRouter(prefix="/notifications")


@router.post("/{notification_id}/delete")
def delete_notification_action(
    request: Request,
    notification_id: str,
    next_url: str = Form(""),
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message = delete_notification(notification_id=notification_id, user_id=user["id"])
    target = next_url if next_url.startswith("/") and not next_url.startswith("//") else request.headers.get("referer", "")
    if not target or not str(target).startswith("/"):
        target = f"/{user['role']}/dashboard"
    separator = "&" if "?" in target else "?"
    field = "message" if ok else "error"
    return RedirectResponse(f"{target}{separator}{urlencode({field: message})}", status_code=303)
