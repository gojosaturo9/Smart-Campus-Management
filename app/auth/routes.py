from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.auth.session import clear_login_session, set_login_session
from app.core.audit import audit_event
from app.core.module_autostart import autostart_modules_for_role
from app.core.roles import ADMIN, ALUMNI, ROLE_HOME, ROLE_LABELS, STUDENT, TEACHER
from app.core.templates import templates
from app.core.users import authenticate_user, create_alumni_signup

router = APIRouter()

LOGIN_ROLES = {
    STUDENT: {
        "title": "Student Portal",
        "description": "Face attendance, timetable, events, ATS, and study modules.",
        "email": "student@campus.local",
        "password": "Student@123",
        "action": "Enter Student Portal",
        "face_login_url": "/attendance/face-login",
        "signup_url": "/attendance/signup",
        "signup_label": "Create student face account",
    },
    TEACHER: {
        "title": "Teacher Portal",
        "description": "Attendance classes, teaching profile, timetable, and classroom modules.",
        "email": "teacher@campus.local",
        "password": "Teacher@123",
        "action": "Enter Teacher Portal",
    },
    ADMIN: {
        "title": "Admin Portal",
        "description": "Users, analytics, timetable setup, module launcher, and campus controls.",
        "email": "admin@campus.local",
        "password": "Admin@123",
        "action": "Enter Admin Portal",
    },
    ALUMNI: {
        "title": "Alumni Portal",
        "description": "Student connect, guidance posts, jobs, internships, and meetups.",
        "email": "alumni@campus.local",
        "password": "Alumni@123",
        "action": "Enter Alumni Portal",
        "signup_url": "/alumni/signup",
        "signup_label": "Apply as alumni mentor",
    },
}


@router.get("/")
def root(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(ROLE_HOME[user["role"]], status_code=303)
    return RedirectResponse("/login", status_code=303)


@router.get("/login")
def login_page(request: Request, role: str = ""):
    selected_role = role if role in LOGIN_ROLES else ""
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "error": None,
            "roles": LOGIN_ROLES,
            "selected_role": selected_role,
            "selected": LOGIN_ROLES.get(selected_role),
        },
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    selected_role = role if role in LOGIN_ROLES else ""
    if not selected_role:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Select a portal before signing in.",
                "roles": LOGIN_ROLES,
                "selected_role": "",
                "selected": None,
            },
            status_code=400,
        )

    user = authenticate_user(email, password)
    if not user:
        audit_event("auth.login_failed", request=request, email=email.strip().lower())
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Invalid email/password or inactive account.",
                "roles": LOGIN_ROLES,
                "selected_role": selected_role,
                "selected": LOGIN_ROLES[selected_role],
            },
            status_code=400,
        )
    if user["role"] != selected_role:
        audit_event("auth.login_role_mismatch", request=request, email=email.strip().lower(), selected_role=selected_role, actual_role=user["role"])
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": f"This account belongs to the {ROLE_LABELS[user['role']]} portal. Select the correct role box.",
                "roles": LOGIN_ROLES,
                "selected_role": selected_role,
                "selected": LOGIN_ROLES[selected_role],
            },
            status_code=403,
        )

    set_login_session(request, user)
    started = autostart_modules_for_role(user["role"])
    audit_event("auth.login_success", user=user, request=request)
    if started:
        audit_event("modules.autostart", user=user, request=request, started=started)
    return RedirectResponse(ROLE_HOME[user["role"]], status_code=303)


@router.get("/alumni/signup")
def alumni_signup_page(request: Request):
    return templates.TemplateResponse(
        "auth/alumni_signup.html",
        {"request": request, "error": "", "created": ""},
    )


@router.post("/alumni/signup")
def alumni_signup_action(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    graduation_year: str = Form(...),
    company: str = Form(...),
    job_title: str = Form(...),
    linkedin_url: str = Form(""),
    bio: str = Form(""),
):
    ok, message = create_alumni_signup(
        name=name,
        email=email,
        password=password,
        graduation_year=graduation_year,
        company=company,
        job_title=job_title,
        linkedin_url=linkedin_url,
        bio=bio,
    )
    audit_event(
        "auth.alumni_signup",
        request=request,
        email=email.strip().lower(),
        ok=ok,
        message=message,
    )
    return templates.TemplateResponse(
        "auth/alumni_signup.html",
        {"request": request, "error": "" if ok else message, "created": message if ok else ""},
        status_code=200 if ok else 400,
    )


@router.post("/logout")
def logout(request: Request):
    audit_event("auth.logout", user=request.session.get("user"), request=request)
    clear_login_session(request)
    return RedirectResponse("/login", status_code=303)


@router.get("/forbidden")
def forbidden(request: Request, needed: str = ""):
    return templates.TemplateResponse(
        "errors/forbidden.html",
        {"request": request, "needed": needed},
        status_code=403,
    )
