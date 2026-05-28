from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.supabase_client import eq, rest_delete, rest_insert, rest_select


def save_analysis(user_id: str, filename: str, analysis_result: dict[str, Any]) -> str:
    serializable_result = json.loads(json.dumps(analysis_result, default=_json_default))
    inserted = rest_insert(
        "analyses",
        {
            "user_id": user_id,
            "filename": filename,
            "ats_score": serializable_result.get("ats_score", 0),
            "keyword_match": serializable_result.get("keyword_match", 0),
            "missing_keywords": serializable_result.get("missing_keywords", []),
            "analysis_result": serializable_result,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return str(inserted[0].get("id")) if inserted else ""


def get_user_history(user_id: str) -> list[dict[str, Any]]:
    rows = rest_select(
        "analyses",
        {
            "select": "*",
            "user_id": eq(user_id),
            "order": "created_at.desc",
        },
    )
    return [_history_row(row) for row in rows]


def get_analysis(analysis_id: str, user_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "analyses",
        {
            "select": "*",
            "id": eq(analysis_id),
            "user_id": eq(user_id),
            "limit": "1",
        },
    )
    return _history_row(rows[0]) if rows else None


def delete_analysis(analysis_id: str, user_id: str) -> bool:
    deleted = rest_delete(
        "analyses",
        {
            "id": eq(analysis_id),
            "user_id": eq(user_id),
        },
    )
    return bool(deleted)


def _history_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id")),
        "filename": row.get("filename") or "resume",
        "resume_name": row.get("filename") or "resume",
        "job_title": "Software Engineer",
        "ats_score": row.get("ats_score", 0),
        "keyword_match": row.get("keyword_match", 0),
        "missing_keywords": row.get("missing_keywords", []),
        "date": row.get("created_at", ""),
        "created_at": row.get("created_at", ""),
        "analysis_result": row.get("analysis_result", {}),
    }


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)
