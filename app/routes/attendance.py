from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from urllib.parse import urlencode

from app.auth.session import get_current_user, require_role, set_login_session
from app.core.attendance import (
    admin_attendance_analytics_context,
    admin_attendance_analytics_csv,
    analyze_class_attendance,
    attendance_context,
    attendance_review_context,
    face_login,
    register_student,
    save_reviewed_attendance,
    signup_context,
    student_attendance_details,
    student_attendance_report_csv,
    teacher_attendance_report_csv,
    teacher_attendance_history,
    teacher_attendance_history_csv,
    teacher_attendance_session_csv,
    teacher_attendance_session_detail,
    teacher_session_result,
)
from app.core.audit import audit_event
from app.core.profile_photo import save_profile_photo
from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.templates import templates

router = APIRouter(prefix="/attendance")

NO_FACE_MATCH_MESSAGE = "Face was captured, but no matching student profile was found."


@router.get("")
def attendance_page(
    request: Request,
    message: str = "",
    error: str = "",
    session_id: str = "",
    review_token: str = "",
    user: dict = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "attendance/index.html",
        {
            "request": request,
            "user": user,
            "context": attendance_context(user),
            "session_result": teacher_session_result(user, session_id),
            "review": attendance_review_context(user, review_token),
            "message": message,
            "error": error,
        },
    )


@router.get("/profile-photo")
def student_profile_photo(user: dict = Depends(require_role(STUDENT))):
    return RedirectResponse("/profile/photo", status_code=303)


@router.post("/profile-photo")
async def update_student_profile_photo(
    request: Request,
    profile_photo: UploadFile | None = File(None),
    user: dict = Depends(require_role(STUDENT)),
):
    image_bytes = await profile_photo.read() if profile_photo and profile_photo.filename else None
    ok, message = save_profile_photo(user["id"], image_bytes)
    audit_event("attendance.profile_photo_update", user=user, request=request, ok=ok, message=message)
    field = "message" if ok else "error"
    return RedirectResponse(f"/attendance?{urlencode({field: message})}", status_code=303)


@router.post("/teacher/mark")
async def teacher_mark_attendance_action(
    request: Request,
    class_choice: str = Form(...),
    source: str = Form("upload"),
    class_photo: list[UploadFile] | None = File(None),
    user: dict = Depends(require_role(TEACHER)),
):
    subject_id, section_id, slot_label, starts_at, ends_at = _split_class_choice(class_choice)
    image_bytes_list = []
    for photo in class_photo or []:
        if photo and photo.filename:
            image_bytes_list.append(await photo.read())
    result = analyze_class_attendance(
        teacher=user,
        subject_id=subject_id,
        section_id=section_id,
        image_bytes_list=image_bytes_list,
        source=source,
        slot_label=slot_label,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    audit_event("attendance.teacher_analyze", user=user, request=request, ok=result.ok, message=result.message)
    if result.ok and result.details:
        params = {"review_token": str(result.details.get("review_token") or "")}
    else:
        params = {"error": result.message}
    return RedirectResponse(f"/attendance?{urlencode(params)}", status_code=303)


@router.post("/teacher/confirm")
async def teacher_confirm_attendance_action(
    request: Request,
    review_token: str = Form(...),
    update_existing: str = Form(""),
    user: dict = Depends(require_role(TEACHER)),
):
    form = await request.form()
    final_statuses = {}
    correction_reasons = {}
    for key, value in form.multi_items():
        if key.startswith("status_"):
            final_statuses[key.removeprefix("status_")] = str(value)
        if key.startswith("reason_"):
            correction_reasons[key.removeprefix("reason_")] = str(value)
    result = save_reviewed_attendance(
        teacher=user,
        review_token=review_token,
        final_statuses=final_statuses,
        correction_reasons=correction_reasons,
        update_existing=update_existing == "yes",
    )
    audit_event("attendance.teacher_confirm", user=user, request=request, ok=result.ok, message=result.message)
    if result.ok and result.details:
        params = {
            "message": result.message,
            "attendance_session_id": str(result.details.get("session_id") or ""),
        }
        return RedirectResponse(f"/teacher/dashboard?{urlencode(params)}", status_code=303)
    else:
        params = {"error": result.message}
        params["review_token"] = review_token
    return RedirectResponse(f"/attendance?{urlencode(params)}", status_code=303)


@router.get("/teacher/report.csv")
def teacher_report_csv(user: dict = Depends(require_role(TEACHER))):
    return Response(
        teacher_attendance_report_csv(user),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance-report.csv"},
    )


@router.get("/student/details")
def student_attendance_details_page(request: Request, user: dict = Depends(require_role(STUDENT))):
    return templates.TemplateResponse(
        "attendance/student_details.html",
        {
            "request": request,
            "user": user,
            "context": student_attendance_details(user),
        },
    )


@router.get("/student/report.csv")
def student_attendance_details_csv(user: dict = Depends(require_role(STUDENT))):
    return Response(
        student_attendance_report_csv(user),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student-attendance-report.csv"},
    )


@router.get("/teacher/history")
def teacher_attendance_history_page(request: Request, user: dict = Depends(require_role(TEACHER))):
    return templates.TemplateResponse(
        "attendance/teacher_history.html",
        {
            "request": request,
            "user": user,
            "context": teacher_attendance_history(user),
        },
    )


@router.get("/teacher/history.csv")
def teacher_attendance_history_export(user: dict = Depends(require_role(TEACHER))):
    return Response(
        teacher_attendance_history_csv(user),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=teacher-attendance-history.csv"},
    )


@router.get("/teacher/session/{session_id}")
def teacher_attendance_session_page(request: Request, session_id: str, user: dict = Depends(require_role(TEACHER, ADMIN))):
    detail = teacher_attendance_session_detail(user, session_id)
    if not detail:
        return RedirectResponse(f"/attendance?{urlencode({'error': 'Attendance session was not found.'})}", status_code=303)
    return templates.TemplateResponse(
        "attendance/session_detail.html",
        {
            "request": request,
            "user": user,
            "detail": detail,
        },
    )


@router.get("/teacher/session/{session_id}/report.csv")
def teacher_attendance_session_export(session_id: str, user: dict = Depends(require_role(TEACHER, ADMIN))):
    return Response(
        teacher_attendance_session_csv(user, session_id),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance-session.csv"},
    )


@router.get("/admin/analytics")
def admin_attendance_analytics_page(request: Request, user: dict = Depends(require_role(ADMIN))):
    return templates.TemplateResponse(
        "attendance/admin_analytics.html",
        {
            "request": request,
            "user": user,
            "context": admin_attendance_analytics_context(),
        },
    )


@router.get("/admin/analytics.csv")
def admin_attendance_analytics_export(user: dict = Depends(require_role(ADMIN))):
    return Response(
        admin_attendance_analytics_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admin-attendance-analytics.csv"},
    )


@router.get("/signup")
def student_signup_page(request: Request, message: str = "", error: str = ""):
    return templates.TemplateResponse(
        "attendance/signup.html",
        {
            "request": request,
            "context": signup_context(),
            "message": message,
            "error": error,
        },
    )


@router.post("/signup")
async def student_signup_action(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    roll_number: str = Form(...),
    department_id: str = Form(...),
    branch_id: str = Form(...),
    semester: str = Form(...),
    section_name: str = Form(...),
    academic_year: str = Form(...),
    face_photo: UploadFile | None = File(None),
):
    face_bytes = await face_photo.read() if face_photo and face_photo.filename else None
    result = register_student(
        name=name,
        email=email,
        password=password,
        roll_number=roll_number,
        department_id=department_id,
        branch_id=branch_id,
        semester=semester,
        section_name=section_name,
        academic_year=academic_year,
        face_bytes=face_bytes,
    )
    audit_event("attendance.student_signup", request=request, email=email.strip().lower(), ok=result.ok, message=result.message)
    if result.ok and result.user:
        set_login_session(request, result.user)
        return RedirectResponse(f"/attendance?{urlencode({'message': result.message})}", status_code=303)
    return RedirectResponse(f"/attendance/signup?{urlencode({'error': result.message})}", status_code=303)


@router.get("/face-login")
def face_login_page(request: Request, error: str = ""):
    return templates.TemplateResponse(
        "attendance/face_login.html",
        {
            "request": request,
            "error": error,
        },
    )


@router.post("/face-login")
async def face_login_action(request: Request, face_photo: UploadFile | None = File(None)):
    face_bytes = await face_photo.read() if face_photo and face_photo.filename else None
    result = face_login(face_bytes)
    audit_event("attendance.face_login", request=request, ok=result.ok, message=result.message)
    if result.ok and result.user:
        set_login_session(request, result.user)
        return RedirectResponse(f"/attendance?{urlencode({'message': result.message})}", status_code=303)
    if result.message == NO_FACE_MATCH_MESSAGE and result.face_embedding:
        params = urlencode({"message": "Face not recognized. Complete signup with a fresh live scan to create your student account."})
        return RedirectResponse(f"/attendance/signup?{params}", status_code=303)
    return RedirectResponse(f"/attendance/face-login?{urlencode({'error': result.message})}", status_code=303)


def _split_class_choice(value: str) -> tuple[str, str, str, str, str]:
    parts = str(value or "").split("|")
    if len(parts) < 2:
        return "", "", "", "", ""
    parts += [""] * (5 - len(parts))
    return parts[0], parts[1], parts[2], parts[3], parts[4]
