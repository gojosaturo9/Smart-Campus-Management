from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.auth.routes import router as auth_router
from app.core.config import settings
from app.core.errors import http_exception_handler, unhandled_exception_handler
from app.routes.dashboard import router as dashboard_router
from app.routes.admin import router as admin_router
from app.routes.alumni import router as alumni_router
from app.routes.attendance import router as attendance_router
from app.routes.events import router as events_router
from app.routes.modules import router as modules_router
from app.routes.profile import router as profile_router
from app.routes.teacher import router as teacher_router
from app.routes.timetable import router as timetable_router


def create_app() -> FastAPI:
    settings.validate_startup()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        same_site="lax",
        https_only=settings.session_https_only,
    )
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(alumni_router)
    app.include_router(attendance_router)
    app.include_router(events_router)
    app.include_router(modules_router)
    app.include_router(profile_router)
    app.include_router(teacher_router)
    app.include_router(timetable_router)

    return app


app = create_app()
