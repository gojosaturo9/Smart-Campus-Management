from __future__ import annotations

from ast import literal_eval

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.auth.session import get_current_user, set_login_session
from app.core.attendance import attendance_context, face_login, register_student, signup_context
from app.core.audit import audit_event
from app.core.templates import templates

router = APIRouter(prefix="/attendance")

NO_FACE_MATCH_MESSAGE = "Face was captured, but no matching student profile was found."
PENDING_FACE_KEY = "pending_student_face_embedding"


@router.get("")
def attendance_page(
    request: Request,
    message: str = "",
    error: str = "",
    user: dict = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "attendance/index.html",
        {
            "request": request,
            "user": user,
            "context": attendance_context(user),
            "message": message,
            "error": error,
        },
    )


@router.get("/signup")
def student_signup_page(request: Request, message: str = "", error: str = ""):
    pending_face = bool(_pending_face_embedding(request))
    return templates.TemplateResponse(
        "attendance/signup.html",
        {
            "request": request,
            "context": signup_context(),
            "message": message,
            "error": error,
            "pending_face": pending_face,
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
    pending_embedding = _pending_face_embedding(request) if not face_bytes else None
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
        face_embedding=pending_embedding,
    )
    audit_event("attendance.student_signup", request=request, email=email.strip().lower(), ok=result.ok, message=result.message)
    if result.ok and result.user:
        request.session.pop(PENDING_FACE_KEY, None)
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
        request.session.pop(PENDING_FACE_KEY, None)
        set_login_session(request, result.user)
        return RedirectResponse(f"/attendance?{urlencode({'message': result.message})}", status_code=303)
    if result.message == NO_FACE_MATCH_MESSAGE and result.face_embedding:
        request.session[PENDING_FACE_KEY] = repr(result.face_embedding)
        params = urlencode({"message": "Face not recognized. Complete signup to create your student account with this live scan."})
        return RedirectResponse(f"/attendance/signup?{params}", status_code=303)
    return RedirectResponse(f"/attendance/face-login?{urlencode({'error': result.message})}", status_code=303)


def _pending_face_embedding(request: Request) -> list[float] | None:
    value = request.session.get(PENDING_FACE_KEY)
    if not value:
        return None
    try:
        embedding = literal_eval(value)
    except (SyntaxError, ValueError):
        request.session.pop(PENDING_FACE_KEY, None)
        return None
    if not isinstance(embedding, list) or len(embedding) != 128:
        request.session.pop(PENDING_FACE_KEY, None)
        return None
    try:
        return [float(item) for item in embedding]
    except (TypeError, ValueError):
        request.session.pop(PENDING_FACE_KEY, None)
        return None
