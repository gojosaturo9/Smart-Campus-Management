from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import quote

from app.auth.session import get_current_user, require_role
from app.core.audit import audit_event
from app.core.roles import ADMIN
from app.core.templates import templates
from app.core.timetable_generator import generate_timetable
from app.core.timetable_view import latest_timetable_for_user

router = APIRouter(prefix="/timetable")


@router.get("")
def timetable_page(
    request: Request,
    day: str = "",
    user: dict = Depends(get_current_user),
):
    timetable = latest_timetable_for_user(user, day)
    return templates.TemplateResponse(
        "timetable/latest.html",
        {
            "request": request,
            "user": user,
            "timetable": timetable,
            "message": request.query_params.get("message", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/generate")
def generate_timetable_action(
    request: Request,
    user: dict = Depends(require_role(ADMIN)),
):
    result = generate_timetable(str(user["id"]))
    audit_event("timetable.generate", user=user, request=request, ok=result.ok, message=result.message)
    detail = result.message
    if result.ok:
        detail += f" Sections: {result.sections}, teachers: {result.teachers}, subjects: {result.subjects}."
    field = "message" if result.ok else "error"
    return RedirectResponse(
        url=f"/timetable?{field}={quote(detail)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
