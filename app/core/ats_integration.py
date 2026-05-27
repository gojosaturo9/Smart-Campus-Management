from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass(frozen=True)
class AtsSummary:
    status: str
    total_analyses: int = 0
    latest_score: float | None = None
    latest_resume: str = ""
    latest_date: str = ""
    message: str = ""


def get_ats_summary(access_token: str) -> AtsSummary:
    api_url = settings.env("ATS_BACKEND_URL")
    if not api_url:
        return AtsSummary(status="not configured", message="ATS backend URL is not configured.")
    if not access_token:
        return AtsSummary(status="not signed in", message="Supabase access token is missing.")

    try:
        request = Request(
            api_url.rstrip("/") + "/api/v1/history",
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "SmartCampusATS/1.0",
            },
        )
        with urlopen(request, timeout=2.5) as response:
            history = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return AtsSummary(status="error", message=f"ATS backend returned HTTP {exc.code}.")
    except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
        return AtsSummary(status="offline", message=str(exc))

    if not isinstance(history, list) or not history:
        return AtsSummary(status="ready", message="No resume analyses yet.")

    latest = history[0]
    return AtsSummary(
        status="ready",
        total_analyses=len(history),
        latest_score=_score(latest),
        latest_resume=latest.get("resume_name") or latest.get("filename") or "Resume",
        latest_date=latest.get("created_at") or latest.get("date") or "",
        message="Latest ATS analysis loaded.",
    )


def _score(row: dict) -> float | None:
    value = row.get("ats_score")
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None
