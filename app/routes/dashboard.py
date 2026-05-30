from fastapi import APIRouter, Depends, Request

from app.auth.session import require_role
from app.core.module_catalog import list_modules_for_role
from app.core.roles import ADMIN, ALUMNI, STUDENT, TEACHER
from app.core.templates import templates
from app.core.users import user_counts_by_role

router = APIRouter()


@router.get("/student/dashboard")
def student_dashboard(request: Request, user=Depends(require_role(STUDENT))):
    return _dashboard(request, user, "Student Dashboard")


@router.get("/teacher/dashboard")
def teacher_dashboard(request: Request, user=Depends(require_role(TEACHER))):
    return _dashboard(request, user, "Teacher Dashboard")


@router.get("/admin/dashboard")
def admin_dashboard(request: Request, user=Depends(require_role(ADMIN))):
    return _dashboard(request, user, "Admin Dashboard")


@router.get("/alumni/dashboard")
def alumni_dashboard(request: Request, user=Depends(require_role(ALUMNI))):
    return _dashboard(request, user, "Alumni Dashboard")


def _dashboard(request: Request, user: dict, title: str):
    modules = list_modules_for_role(user["role"])
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "user": user,
            "title": title,
            "modules": modules,
            "user_counts": user_counts_by_role() if user["role"] == ADMIN else {},
        },
    )
