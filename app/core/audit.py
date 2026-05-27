import json
from datetime import datetime, timezone
from typing import Any

from fastapi import Request

from app.core.config import settings


def audit_event(
    action: str,
    user: dict[str, Any] | None = None,
    request: Request | None = None,
    **details: Any,
) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user_id": user.get("id") if user else None,
        "user_email": user.get("email") if user else None,
        "user_role": user.get("role") if user else None,
        "path": str(request.url.path) if request else "",
        "client": request.client.host if request and request.client else "",
        "details": details,
    }
    with settings.audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, default=str, separators=(",", ":")) + "\n")
