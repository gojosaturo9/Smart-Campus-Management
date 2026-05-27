from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.auth.session import get_current_user, require_role
from app.core.alumni import count_posts_by_type, create_alumni_post, list_alumni_posts
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
