from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass(frozen=True)
class NotesSummary:
    status: str
    api_url: str = ""
    health: str = "not configured"
    upload_endpoint: str = ""
    job_endpoint: str = ""
    quiz_endpoint: str = ""
    message: str = ""


def get_notes_summary() -> NotesSummary:
    api_url = settings.env("NOTES_TEST_API_URL")
    if not api_url:
        return NotesSummary(status="not configured", message="Notes-to-Test API URL is not configured.")

    health_url = api_url.rstrip("/") + "/health"
    try:
        request = Request(health_url, headers={"User-Agent": "SmartCampusNotes/1.0"})
        with urlopen(request, timeout=2.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return _summary(api_url, "error", f"Notes-to-Test backend returned HTTP {exc.code}.")
    except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
        return _summary(api_url, "offline", str(exc))

    health = payload.get("status", "unknown") if isinstance(payload, dict) else "unknown"
    status = "ready" if health in {"ok", "healthy"} else "error"
    return _summary(api_url, status, "Notes-to-Test API is reachable.", health=health)


def _summary(api_url: str, status: str, message: str, health: str = "") -> NotesSummary:
    base = api_url.rstrip("/")
    return NotesSummary(
        status=status,
        api_url=api_url,
        health=health or status,
        upload_endpoint=f"{base}/upload/background",
        job_endpoint=f"{base}/jobs/{{job_id}}",
        quiz_endpoint=f"{base}/documents/{{document_id}}/chapters/{{chapter_id}}/quiz",
        message=message,
    )
