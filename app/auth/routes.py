from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.auth.session import clear_login_session, set_login_session
from app.core.roles import ROLE_HOME
from app.core.templates import templates
from app.core.users import authenticate_user

router = APIRouter()


@router.get("/")
def root(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(ROLE_HOME[user["role"]], status_code=303)
    return RedirectResponse("/login", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "error": None},
    )


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = authenticate_user(email, password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Invalid email/password or inactive account.",
            },
            status_code=400,
        )

    set_login_session(request, user)
    return RedirectResponse(ROLE_HOME[user["role"]], status_code=303)


@router.post("/logout")
def logout(request: Request):
    clear_login_session(request)
    return RedirectResponse("/login", status_code=303)


@router.get("/forbidden")
def forbidden(request: Request, needed: str = ""):
    return templates.TemplateResponse(
        "errors/forbidden.html",
        {"request": request, "needed": needed},
        status_code=403,
    )
