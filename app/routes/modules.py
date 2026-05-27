from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import quote

from app.auth.session import get_current_user
from app.core.audit import audit_event
from app.core.ats_integration import get_ats_summary
from app.core.module_processes import (
    get_process_status,
    read_log_tail,
    start_module,
    stop_module,
)
from app.core.module_catalog import MODULES, PLACEHOLDER_MODULES
from app.core.notes_integration import get_notes_summary
from app.core.roles import ADMIN
from app.core.templates import templates
from app.core.timetable_sync import sync_attendance_to_timetable

router = APIRouter(prefix="/modules")


@router.get("")
def modules_overview(
    request: Request,
    user: dict = Depends(get_current_user),
):
    if user["role"] != ADMIN:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=admin"},
        )
    return templates.TemplateResponse(
        "modules/module_launcher.html",
        {
            "request": request,
            "user": user,
            "modules": MODULES.values(),
            "statuses": {key: get_process_status(module) for key, module in MODULES.items()},
        },
    )


@router.get("/{module_key}")
def module_page(
    module_key: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    role = user["role"]

    if module_key in MODULES:
        module = MODULES[module_key]
        if module_key == "attendance":
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/attendance"},
            )
        if module_key == "timetable" and role != ADMIN:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/timetable"},
            )
        if role not in module.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/forbidden"},
            )
        return templates.TemplateResponse(
            "modules/module_detail.html",
            {
                "request": request,
                "user": user,
                "module": module,
                "process_status": get_process_status(module),
                "ats_summary": get_ats_summary(request.session.get("supabase_access_token", ""))
                if module_key == "ats-resume"
                else None,
                "notes_summary": get_notes_summary() if module_key == "notes-to-test" else None,
                "message": request.query_params.get("message", ""),
                "error": request.query_params.get("error", ""),
            },
        )

    if module_key in PLACEHOLDER_MODULES:
        name, allowed_roles = PLACEHOLDER_MODULES[module_key]
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/forbidden"},
            )
        return templates.TemplateResponse(
            "modules/placeholder.html",
            {
                "request": request,
                "user": user,
                "name": name,
                "workspace": _workspace_context(module_key, user),
            },
        )

    raise HTTPException(status_code=404, detail="Module not found")


@router.post("/{module_key}/start")
def start_module_server(
    module_key: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    module = _admin_module(module_key, user)
    ok, message = start_module(module)
    audit_event("module.start", user=user, request=request, module_key=module_key, ok=ok, message=message)
    return _module_redirect(module_key, message, ok)


@router.post("/{module_key}/stop")
def stop_module_server(
    module_key: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    module = _admin_module(module_key, user)
    ok, message = stop_module(module)
    audit_event("module.stop", user=user, request=request, module_key=module_key, ok=ok, message=message)
    return _module_redirect(module_key, message, ok)


@router.post("/timetable/sync-attendance")
def sync_timetable_from_attendance(
    request: Request,
    user: dict = Depends(get_current_user),
):
    if user["role"] != ADMIN:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=admin"},
        )
    result = sync_attendance_to_timetable()
    detail = (
        f"{result.message} Teachers: {result.teachers}, subjects: {result.subjects}, "
        f"departments: {result.departments}, sections: {result.sections}, students: {result.students}."
    )
    audit_event("timetable.sync_attendance", user=user, request=request, ok=result.ok, message=result.message)
    return _module_redirect("timetable", detail, result.ok)


@router.get("/{module_key}/logs")
def module_logs(
    module_key: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    module = _admin_module(module_key, user)
    return templates.TemplateResponse(
        "modules/module_logs.html",
        {
            "request": request,
            "user": user,
            "module": module,
            "process_status": get_process_status(module),
            "log_text": read_log_tail(module),
        },
    )


def _admin_module(module_key: str, user: dict):
    if user["role"] != ADMIN:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=admin"},
        )
    if module_key not in MODULES:
        raise HTTPException(status_code=404, detail="Module not found")
    return MODULES[module_key]


def _module_redirect(module_key: str, message: str, ok: bool):
    field = "message" if ok else "error"
    return RedirectResponse(
        url=f"/modules/{module_key}?{field}={quote(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _workspace_context(module_key: str, user: dict) -> dict:
    contexts = {
        "classroom": {
            "description": "Classroom tools connected to notes, timetable, and attendance workflows.",
            "actions": [
                ("Open Notes-to-Test", "/modules/notes-to-test"),
                ("View Timetable", "/timetable"),
                ("Open Attendance", "/modules/attendance"),
            ],
            "details": [
                ("Signed in as", user["name"]),
                ("Role", user["role"]),
                ("Email", user["email"]),
            ],
        },
        "helpdesk": {
            "description": "Student profile and quick support links for campus services.",
            "actions": [
                ("View Timetable", "/timetable"),
                ("Browse Events", "/events"),
                ("Alumni Opportunities", "/alumni/opportunities"),
            ],
            "details": [
                ("Name", user["name"]),
                ("Email", user["email"]),
                ("Section", user.get("section") or "Auto-detected when timetable data matches"),
                ("Department", user.get("department") or "Not set"),
            ],
        },
        "alumni-meetups": {
            "description": "Use the alumni opportunities page to manage meetups, guidance, jobs, and internships.",
            "actions": [("Open Alumni Opportunities", "/alumni/opportunities")],
            "details": [("Role", user["role"])],
        },
    }
    return contexts.get(
        module_key,
        {
            "description": "This workspace is connected to the Smart Campus role shell.",
            "actions": [("Back to Dashboard", f"/{user['role']}/dashboard")],
            "details": [("Signed in as", user["name"]), ("Role", user["role"])],
        },
    )
