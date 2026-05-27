from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.auth.session import get_current_user, require_role
from app.core.events import (
    create_event,
    list_events,
    register_for_event,
    registered_event_ids,
    registration_counts,
)
from app.core.roles import ADMIN, STUDENT
from app.core.templates import templates

router = APIRouter(prefix="/events")


@router.get("")
def events_page(
    request: Request,
    created: str = "",
    error: str = "",
    user: dict = Depends(get_current_user),
):
    if user["role"] not in {STUDENT, ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=student,admin"},
        )
    return templates.TemplateResponse(
        "events/events.html",
        {
            "request": request,
            "user": user,
            "events": list_events(),
            "registration_counts": registration_counts(),
            "registered_event_ids": registered_event_ids(user["id"]) if user["role"] == STUDENT else set(),
            "created": created,
            "error": error,
        },
    )


@router.post("")
def create_event_action(
    title: str = Form(...),
    description: str = Form(""),
    event_type: str = Form(""),
    starts_at: str = Form(""),
    ends_at: str = Form(""),
    location: str = Form(""),
    user: dict = Depends(require_role(ADMIN)),
):
    ok, message = create_event(
        title=title,
        description=description,
        event_type=event_type,
        starts_at=starts_at,
        ends_at=ends_at,
        location=location,
        created_by=user["id"],
    )
    field = "created" if ok else "error"
    return RedirectResponse(f"/events?{urlencode({field: message})}", status_code=303)


@router.post("/{event_id}/register")
def register_event_action(
    event_id: str,
    user: dict = Depends(require_role(STUDENT)),
):
    ok, message = register_for_event(event_id, user["id"])
    field = "created" if ok else "error"
    return RedirectResponse(f"/events?{urlencode({field: message})}", status_code=303)
