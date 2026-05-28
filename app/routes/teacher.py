from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.auth.session import require_role
from app.core.roles import TEACHER
from app.core.teacher_setup import save_teacher_profile, save_teacher_subject, teacher_setup_context
from app.core.templates import templates

router = APIRouter(prefix="/teacher")


@router.get("/setup")
def setup_page(
    request: Request,
    saved: str = "",
    error: str = "",
    user=Depends(require_role(TEACHER)),
):
    context = teacher_setup_context(user)
    return templates.TemplateResponse(
        "teacher/setup.html",
        {
            "request": request,
            "user": user,
            "saved": saved,
            "error": error,
            **context,
        },
    )


@router.post("/setup/profile")
def save_profile_action(
    employee_code: str = Form(""),
    designation: str = Form(""),
    user=Depends(require_role(TEACHER)),
):
    ok, message = save_teacher_profile(user, employee_code, designation)
    flag = "saved" if ok else "error"
    return RedirectResponse(f"/teacher/setup?{urlencode({flag: message})}", status_code=303)


@router.post("/setup/subjects")
def save_subject_action(
    subject_code: str = Form(...),
    subject_name: str = Form(""),
    department_name: str = Form(""),
    department_code: str = Form(""),
    branch_name: str = Form(""),
    branch_code: str = Form(""),
    semester: str = Form(...),
    section_name: str = Form("A"),
    academic_year: str = Form("2026-27"),
    user=Depends(require_role(TEACHER)),
):
    ok, message = save_teacher_subject(
        user,
        subject_code,
        subject_name,
        department_name,
        department_code,
        branch_name,
        branch_code,
        semester,
        section_name,
        academic_year,
    )
    flag = "saved" if ok else "error"
    return RedirectResponse(f"/teacher/setup?{urlencode({flag: message})}", status_code=303)
