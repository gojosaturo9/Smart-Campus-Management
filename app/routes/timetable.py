from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import quote

from app.auth.session import get_current_user, require_role
from app.core.audit import audit_event
from app.core.roles import ADMIN
from app.core.templates import templates
from app.core.timetable_generator import generate_timetable, publish_timetable
from app.core.timetable_view import DAY_ORDER, latest_timetable_for_user

router = APIRouter(prefix="/timetable")


@router.get("")
def timetable_page(
    request: Request,
    day: str = "",
    run_id: str = "",
    branch: str = "",
    section: str = "",
    user: dict = Depends(get_current_user),
):
    timetable = latest_timetable_for_user(user, day, run_id, branch, section)
    return templates.TemplateResponse(
        "timetable/latest.html",
        {
            "request": request,
            "user": user,
            "timetable": timetable,
            "available_days": [day_name for day_name in DAY_ORDER if day_name not in {"Saturday", "Sunday"}],
            "message": request.query_params.get("message", ""),
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/generate")
def generate_timetable_action(
    request: Request,
    day: str = Form(""),
    user: dict = Depends(require_role(ADMIN)),
):
    result = generate_timetable(str(user["id"]), day)
    audit_event("timetable.generate", user=user, request=request, ok=result.ok, message=result.message)
    detail = result.message
    if result.ok:
        detail += f" Sections: {result.sections}, teachers: {result.teachers}, subjects: {result.subjects}."
    field = "message" if result.ok else "error"
    return RedirectResponse(
        url=f"/timetable?day={quote(day)}&run_id={quote(result.run_id)}&{field}={quote(detail)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/publish")
def publish_timetable_action(
    request: Request,
    run_id: str = Form(...),
    day: str = Form(""),
    user: dict = Depends(require_role(ADMIN)),
):
    result = publish_timetable(run_id)
    audit_event("timetable.publish", user=user, request=request, ok=result.ok, message=result.message)
    field = "message" if result.ok else "error"
    return RedirectResponse(
        url=f"/timetable?day={quote(day)}&run_id={quote(run_id)}&{field}={quote(result.message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
