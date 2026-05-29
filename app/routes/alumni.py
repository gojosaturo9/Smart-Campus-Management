from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from urllib.parse import urlencode

from app.auth.session import get_current_user, require_role
from app.core.alumni import count_posts_by_type, create_alumni_post, list_alumni_posts, delete_alumni_post
from app.core.alumni_mentorship import (
    accept_mentorship_request,
    create_message,
    create_mentorship_request,
    delete_connection_messages_for_user,
    delete_message_for_user,
    edit_message_for_user,
    message_attachment_for_user,
    messages_for_connection,
    mentorship_counts_for_user,
    mentorship_workspace,
    mark_connection_read,
    reject_mentorship_request,
    send_message,
)
from app.core.config import settings
from app.core.roles import ALUMNI, STUDENT, ADMIN
from app.core.templates import templates

router = APIRouter(prefix="/alumni")

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
BLOCKED_ATTACHMENT_SUFFIXES = {".bat", ".cmd", ".com", ".exe", ".js", ".msi", ".ps1", ".scr", ".vbs"}


@router.get("/opportunities")
def opportunities_page(
    request: Request,
    post_type: str = "",
    created: str = "",
    error: str = "",
    user: dict = Depends(get_current_user),
):
    if user["role"] not in {STUDENT, ALUMNI, ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=student,alumni,admin"},
        )
    selected_type = post_type if post_type in {"job", "internship", "guidance"} else ""
    return templates.TemplateResponse(
        "alumni/opportunities.html",
        {
            "request": request,
            "user": user,
            "posts": list_alumni_posts(selected_type),
            "selected_type": selected_type,
            "post_counts": count_posts_by_type(),
            "created": created,
            "error": error,
        },
    )


@router.get("/connect")
def alumni_student_connect_page(
    request: Request,
    user: dict = Depends(get_current_user),
):
    if user["role"] not in {STUDENT, ALUMNI}:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=student,alumni"},
        )
    workspace = mentorship_workspace(user)
    return templates.TemplateResponse(
        "alumni/connect.html",
        {
            "request": request,
            "user": user,
            "workspace": workspace,
            "counts": mentorship_counts_for_user(workspace),
        },
    )


@router.post("/connect/requests")
def create_mentorship_request_action(
    alumni_id: str = Form(...),
    intent: str = Form(...),
    message: str = Form(...),
    user: dict = Depends(require_role(STUDENT)),
):
    ok, response_message = create_mentorship_request(
        student_id=user["id"],
        alumni_id=alumni_id,
        intent=intent,
        message=message,
    )
    field = "message" if ok else "error"
    return RedirectResponse(f"/alumni/connect?{urlencode({field: response_message})}", status_code=303)


@router.post("/connect/requests/{request_id}/accept")
def accept_mentorship_request_action(
    request_id: str,
    user: dict = Depends(require_role(ALUMNI)),
):
    ok, response_message = accept_mentorship_request(request_id=request_id, alumni_id=user["id"])
    field = "message" if ok else "error"
    return RedirectResponse(f"/alumni/connect?{urlencode({field: response_message})}", status_code=303)


@router.post("/connect/requests/{request_id}/reject")
def reject_mentorship_request_action(
    request_id: str,
    user: dict = Depends(require_role(ALUMNI)),
):
    ok, response_message = reject_mentorship_request(request_id=request_id, alumni_id=user["id"])
    field = "message" if ok else "error"
    return RedirectResponse(f"/alumni/connect?{urlencode({field: response_message})}", status_code=303)


@router.post("/connect/messages")
async def send_mentorship_message_action(
    connection_id: str = Form(...),
    message: str = Form(""),
    attachment: UploadFile | None = File(None),
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, attachment_result, response_message = await _save_attachment(attachment)
    if not ok:
        return RedirectResponse(f"/alumni/connect?{urlencode({'error': response_message})}", status_code=303)
    ok, response_message = send_message(
        connection_id=connection_id,
        sender_id=user["id"],
        message=message,
        attachment=attachment_result,
    )
    field = "message" if ok else "error"
    return RedirectResponse(f"/alumni/connect?{urlencode({field: response_message})}", status_code=303)


@router.get("/connect/messages/{connection_id}")
def mentorship_messages_api(
    connection_id: str,
    after_id: str = "",
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message, rows = messages_for_connection(
        connection_id=connection_id,
        user_id=user["id"],
        after_id=after_id,
    )
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "messages": rows}, status_code=status_code)


@router.post("/connect/messages.json")
async def send_mentorship_message_api(
    connection_id: str = Form(...),
    message: str = Form(""),
    attachment: UploadFile | None = File(None),
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, attachment_result, response_message = await _save_attachment(attachment)
    if not ok:
        return JSONResponse({"ok": False, "message": response_message, "row": None}, status_code=400)
    ok, message, row = create_message(
        connection_id=connection_id,
        sender_id=user["id"],
        message=message,
        attachment=attachment_result,
    )
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "row": row}, status_code=status_code)


@router.get("/connect/messages/{message_id}/attachment")
def download_mentorship_message_attachment(
    message_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message, row = message_attachment_for_user(message_id=message_id, user_id=user["id"])
    if not ok or not row:
        raise HTTPException(status_code=404, detail=message)
    path = _attachment_path(row["attachment_path"])
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file not found.")
    return FileResponse(
        path,
        media_type=row.get("attachment_content_type") or "application/octet-stream",
        filename=row.get("attachment_filename") or path.name,
    )


@router.post("/connect/messages/{connection_id}/read")
def mark_mentorship_messages_read_api(
    connection_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message = mark_connection_read(connection_id=connection_id, user_id=user["id"])
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message}, status_code=status_code)


@router.post("/connect/messages/{message_id}/delete")
def delete_mentorship_message_api(
    message_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message = delete_message_for_user(message_id=message_id, user_id=user["id"])
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "message_id": message_id}, status_code=status_code)


@router.post("/connect/message-actions/{message_id}/delete")
def delete_mentorship_message_action_api(
    message_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message = delete_message_for_user(message_id=message_id, user_id=user["id"])
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "message_id": message_id}, status_code=status_code)


@router.post("/connect/messages/{message_id}/edit")
async def edit_mentorship_message_api(
    request: Request,
    message_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    payload = await request.json()
    ok, message, row = edit_message_for_user(
        message_id=message_id,
        user_id=user["id"],
        message=str(payload.get("message") or ""),
    )
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "row": row}, status_code=status_code)


@router.post("/connect/message-actions/{message_id}/edit")
async def edit_mentorship_message_action_api(
    request: Request,
    message_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    payload = await request.json()
    ok, message, row = edit_message_for_user(
        message_id=message_id,
        user_id=user["id"],
        message=str(payload.get("message") or ""),
    )
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "row": row}, status_code=status_code)


@router.post("/connect/connections/{connection_id}/messages/delete")
def delete_mentorship_chat_api(
    connection_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message = delete_connection_messages_for_user(connection_id=connection_id, user_id=user["id"])
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "connection_id": connection_id}, status_code=status_code)


@router.post("/posts")
def create_post_action(
    post_type: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    company: str = Form(""),
    apply_url: str = Form(""),
    expires_at: str = Form(""),
    user: dict = Depends(require_role(ALUMNI)),
):
    ok, message = create_alumni_post(
        alumni_id=user["id"],
        post_type=post_type,
        title=title,
        description=description,
        company=company,
        apply_url=apply_url,
        expires_at=expires_at,
    )
    field = "created" if ok else "error"
    return RedirectResponse(f"/alumni/opportunities?{urlencode({field: message})}", status_code=303)


@router.post("/posts/{post_id}/delete")
def delete_post_action(
    post_id: str,
    user: dict = Depends(require_role(ADMIN)),
):
    ok, message = delete_alumni_post(post_id)
    field = "created" if ok else "error"
    return RedirectResponse(f"/alumni/opportunities?{urlencode({field: message})}", status_code=303)


async def _save_attachment(upload: UploadFile | None) -> tuple[bool, dict | None, str]:
    if not upload or not upload.filename:
        return True, None, ""
    original_name = Path(upload.filename).name
    suffix = Path(original_name).suffix.lower()
    if suffix in BLOCKED_ATTACHMENT_SUFFIXES:
        return False, None, "This attachment type is not allowed."
    content = await upload.read()
    if not content:
        return True, None, ""
    if len(content) > MAX_ATTACHMENT_BYTES:
        return False, None, "Attachment must be 10 MB or smaller."
    directory = settings.data_dir / "mentorship_attachments"
    directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    target = directory / stored_name
    target.write_bytes(content)
    return (
        True,
        {
            "filename": original_name,
            "content_type": upload.content_type or "application/octet-stream",
            "size": len(content),
            "path": stored_name,
        },
        "",
    )


def _attachment_path(stored_name: str) -> Path:
    directory = (settings.data_dir / "mentorship_attachments").resolve()
    path = (directory / Path(stored_name).name).resolve()
    if directory not in path.parents and path != directory:
        raise HTTPException(status_code=404, detail="Attachment file not found.")
    return path
