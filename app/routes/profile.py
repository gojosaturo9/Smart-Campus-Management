from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from urllib.parse import urlencode

from app.auth.session import get_current_user
from app.core.audit import audit_event
from app.core.profile_photo import profile_photo_path, save_profile_photo

router = APIRouter(prefix="/profile")


@router.get("/photo")
def profile_photo(user: dict = Depends(get_current_user)):
    path = profile_photo_path(user["id"])
    if not path.exists():
        return _initials_avatar(user)
    return FileResponse(path, media_type="image/jpeg")


@router.post("/photo")
async def update_profile_photo(
    request: Request,
    profile_photo: UploadFile | None = File(None),
    user: dict = Depends(get_current_user),
):
    image_bytes = await profile_photo.read() if profile_photo and profile_photo.filename else None
    ok, message = save_profile_photo(user["id"], image_bytes)
    audit_event("profile.photo_update", user=user, request=request, ok=ok, message=message)
    field = "message" if ok else "error"
    next_url = _safe_next_url(str(request.headers.get("referer") or ""), user["role"])
    separator = "&" if "?" in next_url else "?"
    return RedirectResponse(f"{next_url}{separator}{urlencode({field: message})}", status_code=303)


def _safe_next_url(referer: str, role: str) -> str:
    fallback = f"/{role}/dashboard"
    if not referer:
        return fallback
    value = referer.split("?", 1)[0]
    for prefix in ("http://127.0.0.1:9000", "http://127.0.0.1:9001", "http://127.0.0.1:9002", "http://localhost:9000", "http://localhost:9001", "http://localhost:9002"):
        if value.startswith(prefix):
            value = value[len(prefix):] or fallback
            break
    if not value.startswith("/") or value.startswith("/profile/") or value.startswith("/static/"):
        return fallback
    return value


def _initials_avatar(user: dict) -> Response:
    initials = str(user.get("initials") or "U")[:2].upper()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
<defs>
  <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
    <stop offset="0" stop-color="#5e72e4"/>
    <stop offset="1" stop-color="#11cdef"/>
  </linearGradient>
</defs>
<rect width="160" height="160" rx="80" fill="url(#g)"/>
<text x="80" y="92" text-anchor="middle" font-family="Open Sans, Arial, sans-serif" font-size="54" font-weight="800" fill="#ffffff">{initials}</text>
</svg>"""
    return Response(svg, media_type="image/svg+xml")
