import json
from base64 import b64encode

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner

from app.auth import session as session_module
from app.core.config import settings
from app.main import app


STUDENT_USER = {
    "id": "student-id",
    "name": "Student User",
    "email": "student@campus.local",
    "role": "student",
    "is_active": True,
}


def test_ats_requires_login():
    client = TestClient(app, follow_redirects=False)

    response = client.get("/ats")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_student_can_open_internal_ats_home(monkeypatch):
    monkeypatch.setattr(session_module, "get_user_by_id", lambda user_id: STUDENT_USER)
    monkeypatch.setattr("app.routes.ats.get_user_history", lambda user_id: [])
    client = TestClient(app, follow_redirects=False)
    _set_session(client, {"user_id": "student-id"})

    response = client.get("/ats")

    assert response.status_code == 200
    assert "Resume Analysis" in response.text
    assert 'action="/ats/analyze"' in response.text


def test_ats_module_redirects_to_internal_route(monkeypatch):
    monkeypatch.setattr(session_module, "get_user_by_id", lambda user_id: STUDENT_USER)
    client = TestClient(app, follow_redirects=False)
    _set_session(client, {"user_id": "student-id"})

    response = client.get("/modules/ats-resume")

    assert response.status_code == 303
    assert response.headers["location"] == "/ats"


def _set_session(client: TestClient, session: dict) -> None:
    data = b64encode(json.dumps(session).encode("utf-8"))
    cookie = TimestampSigner(settings.session_secret).sign(data).decode("utf-8")
    client.cookies.set("session", cookie)
