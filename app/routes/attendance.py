from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.auth.session import get_current_user, require_role, set_login_session
from app.core.attendance import attendance_context, face_login, mark_class_attendance, register_student, signup_context, teacher_session_result
from app.core.audit import audit_event
from app.core.profile_photo import save_profile_photo
from app.core.roles import STUDENT, TEACHER
from app.core.templates import templates

router = APIRouter(prefix="/attendance")

NO_FACE_MATCH_MESSAGE = "Face was captured, but no matching student profile was found."


@router.get("")
def attendance_page(
    request: Request,
    message: str = "",
    error: str = "",
    session_id: str = "",
    user: dict = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "attendance/index.html",
        {
            "request": request,
            "user": user,
            "context": attendance_context(user),
            "session_result": teacher_session_result(user, session_id),
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
    class_photo: UploadFile | None = File(None),
    user: dict = Depends(require_role(TEACHER)),
):
    subject_id, section_id = _split_class_choice(class_choice)
    image_bytes = await class_photo.read() if class_photo and class_photo.filename else None
    result = mark_class_attendance(
        teacher=user,
        subject_id=subject_id,
        section_id=section_id,
        image_bytes=image_bytes,
        source=source,
    )
    audit_event("attendance.teacher_mark", user=user, request=request, ok=result.ok, message=result.message)
    field = "message" if result.ok else "error"
    params = {field: result.message}
    if result.ok and result.details:
        params["session_id"] = str(result.details.get("session_id") or "")
    return RedirectResponse(f"/attendance?{urlencode(params)}", status_code=303)


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


def _split_class_choice(value: str) -> tuple[str, str]:
    parts = str(value or "").split("|", 1)
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1]
