from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from urllib.parse import urlencode

from app.auth.session import get_current_user, require_role
from app.core.alumni import count_posts_by_type, create_alumni_post, list_alumni_posts
from app.core.alumni_mentorship import (
    accept_mentorship_request,
    create_message,
    create_mentorship_request,
    messages_for_connection,
    mentorship_counts_for_user,
    mentorship_workspace,
    mark_connection_read,
    reject_mentorship_request,
    send_message,
)
from app.core.roles import ALUMNI, STUDENT
from app.core.templates import templates

router = APIRouter(prefix="/alumni")


@router.get("/opportunities")
def opportunities_page(
    request: Request,
    post_type: str = "",
    created: str = "",
    error: str = "",
    user: dict = Depends(get_current_user),
):
    if user["role"] not in {STUDENT, ALUMNI}:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/forbidden?needed=student,alumni"},
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
def send_mentorship_message_action(
    connection_id: str = Form(...),
    message: str = Form(...),
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, response_message = send_message(connection_id=connection_id, sender_id=user["id"], message=message)
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
    request: Request,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    payload = await request.json()
    ok, message, row = create_message(
        connection_id=str(payload.get("connection_id") or ""),
        sender_id=user["id"],
        message=str(payload.get("message") or ""),
    )
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message, "row": row}, status_code=status_code)


@router.post("/connect/messages/{connection_id}/read")
def mark_mentorship_messages_read_api(
    connection_id: str,
    user: dict = Depends(require_role(STUDENT, ALUMNI)),
):
    ok, message = mark_connection_read(connection_id=connection_id, user_id=user["id"])
    status_code = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message}, status_code=status_code)


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
