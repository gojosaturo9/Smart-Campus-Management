from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.routes import router as auth_router
from app.core.config import settings
from app.core.db import initialize_database
from app.routes.dashboard import router as dashboard_router
from app.routes.admin import router as admin_router
from app.routes.modules import router as modules_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        same_site="lax",
        https_only=False,
    )

    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(modules_router)

    @app.on_event("startup")
    def startup() -> None:
        initialize_database()

    return app


app = create_app()
