from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.templates import templates


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    location = exc.headers.get("Location") if exc.headers else None
    if 300 <= exc.status_code < 400 and location:
        return RedirectResponse(location, status_code=exc.status_code)

    if exc.status_code == 403:
        return templates.TemplateResponse(
            "errors/forbidden.html",
            {"request": request, "needed": request.query_params.get("needed", "")},
            status_code=403,
        )

    if exc.status_code == 404:
        return templates.TemplateResponse(
            "errors/not_found.html",
            {"request": request},
            status_code=404,
        )

    return templates.TemplateResponse(
        "errors/server_error.html",
        {"request": request},
        status_code=exc.status_code,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "errors/server_error.html",
        {"request": request},
        status_code=500,
    )
