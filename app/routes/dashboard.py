from fastapi import APIRouter, Depends, Request

from app.auth.session import require_role
from app.core.analytics import admin_analytics_cards
from app.core.dashboard_cards import cards_for_role
from app.core.dashboard_summary import dashboard_summary_for_user
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
    return templates.TemplateResponse(
        "alumni/dashboard.html",
        {
            "request": request,
            "user": user,
        },
    )


def _dashboard(request: Request, user: dict, title: str):
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "user": user,
            "title": title,
            "dashboard_cards": cards_for_role(user["role"]),
            "analytics_cards": admin_analytics_cards() if user["role"] == ADMIN else (),
            "dashboard_summary": dashboard_summary_for_user(user),
            "user_counts": user_counts_by_role() if user["role"] == ADMIN else {},
        },
    )
