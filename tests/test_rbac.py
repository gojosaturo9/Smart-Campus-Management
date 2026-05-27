from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.auth import session as session_module
from app.auth.session import require_role


ADMIN_USER = {
    "id": "admin-id",
    "name": "Admin User",
    "email": "admin@campus.local",
    "role": "admin",
    "is_active": True,
}

STUDENT_USER = {
    "id": "student-id",
    "name": "Student User",
    "email": "student@campus.local",
    "role": "student",
    "is_active": True,
}


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @app.get("/admin-only")
    def admin_only(user=Depends(require_role("admin"))):
        return {"role": user["role"]}

    @app.get("/student-only")
    def student_only(user=Depends(require_role("student"))):
        return {"role": user["role"]}

    @app.get("/test-login/{user_id}")
    def test_login(user_id: str, request: Request):
        request.session["user_id"] = user_id
        return {"ok": True}

    return app


def set_session(client: TestClient, user_id: str) -> None:
    response = client.get(f"/test-login/{user_id}")
    assert response.status_code == 200


def test_unauthenticated_user_redirects_to_login(monkeypatch):
    monkeypatch.setattr(session_module, "get_user_by_id", lambda user_id: None)
    client = TestClient(build_test_app(), follow_redirects=False)

    response = client.get("/admin-only")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_admin_can_access_admin_route(monkeypatch):
    monkeypatch.setattr(session_module, "get_user_by_id", lambda user_id: ADMIN_USER)
    client = TestClient(build_test_app(), follow_redirects=False)
    set_session(client, "admin-id")

    response = client.get("/admin-only")

    assert response.status_code == 200
    assert response.json() == {"role": "admin"}


def test_student_cannot_access_admin_route(monkeypatch):
    monkeypatch.setattr(session_module, "get_user_by_id", lambda user_id: STUDENT_USER)
    client = TestClient(build_test_app(), follow_redirects=False)
    set_session(client, "student-id")

    response = client.get("/admin-only")

    assert response.status_code == 303
    assert response.headers["location"] == "/forbidden?needed=admin"
