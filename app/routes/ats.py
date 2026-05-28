from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse, Response

from app.auth.session import require_role
from app.core.ats.database.analyses import (
    delete_analysis,
    get_analysis,
    get_user_history,
    save_analysis,
)
from app.core.ats.runtime import get_ats_models
from app.core.roles import STUDENT
from app.core.templates import templates

router = APIRouter(prefix="/ats")


@router.get("")
def ats_home(request: Request, user: dict = Depends(require_role(STUDENT))):
    return _render_home(request, user)


@router.post("/analyze")
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(...),
    analysis_mode: str = Form("general"),
    job_description: str = Form(""),
    user: dict = Depends(require_role(STUDENT)),
):
    filename = resume.filename or "resume"
    file_bytes = await resume.read()
    jd_text = job_description.strip() if analysis_mode == "jd" else ""

    try:
        from app.core.ats.services.resume_analyzer import analyze_full_resume
        from app.core.ats.services.resume_parser import parse_resume_file

        resume_text, _metadata = parse_resume_file(file_bytes, filename)
        nlp, embedder = get_ats_models()
        result = analyze_full_resume(
            resume_text=resume_text,
            nlp=nlp,
            embedder=embedder,
            job_description=jd_text,
        )
        result = _plain(result)
        analysis_id = save_analysis(user["id"], filename, result)
    except Exception as exc:
        return _render_home(
            request,
            user,
            error=f"ATS analysis failed: {exc}",
            form={"analysis_mode": analysis_mode, "job_description": job_description},
        )

    return _render_home(
        request,
        user,
        result=result,
        analysis_id=analysis_id,
        success="Resume analysis saved to your ATS history.",
        form={"analysis_mode": analysis_mode, "job_description": job_description},
    )


@router.get("/history")
def ats_history(request: Request, user: dict = Depends(require_role(STUDENT))):
    return templates.TemplateResponse(
        "ats/history.html",
        {
            "request": request,
            "user": user,
            "history": _history(user),
        },
    )


@router.get("/history/{analysis_id}")
def ats_history_detail(
    analysis_id: str,
    request: Request,
    user: dict = Depends(require_role(STUDENT)),
):
    row = get_analysis(analysis_id, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _render_home(
        request,
        user,
        result=row.get("analysis_result") or {},
        analysis_id=analysis_id,
        history_item=row,
    )


@router.post("/history/{analysis_id}/delete")
def ats_delete_history(analysis_id: str, user: dict = Depends(require_role(STUDENT))):
    delete_analysis(analysis_id, user["id"])
    return RedirectResponse("/ats/history?message=Analysis deleted", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/history/{analysis_id}/report.pdf")
def ats_history_pdf(analysis_id: str, user: dict = Depends(require_role(STUDENT))):
    row = get_analysis(analysis_id, user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _pdf_response(row.get("analysis_result") or {}, f"ats_report_{analysis_id}.pdf")


@router.post("/report.pdf")
async def ats_pdf_from_result(
    analysis_json: str = Form(...),
    user: dict = Depends(require_role(STUDENT)),
):
    try:
        data = json.loads(analysis_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid report payload") from exc
    return _pdf_response(data, "ats_report.pdf")


def _render_home(
    request: Request,
    user: dict,
    *,
    result: dict[str, Any] | None = None,
    analysis_id: str = "",
    history_item: dict[str, Any] | None = None,
    error: str = "",
    success: str = "",
    form: dict[str, str] | None = None,
):
    return templates.TemplateResponse(
        "ats/index.html",
        {
            "request": request,
            "user": user,
            "result": result,
            "analysis_id": analysis_id,
            "history_item": history_item,
            "history": _history(user, limit=5),
            "error": error,
            "success": success,
            "form": form or {"analysis_mode": "general", "job_description": ""},
            "analysis_json": json.dumps(result or {}, default=str),
        },
    )


def _history(user: dict, limit: int | None = None) -> list[dict[str, Any]]:
    rows = get_user_history(user["id"])
    return rows[:limit] if limit else rows


def _pdf_response(data: dict[str, Any], filename: str) -> Response:
    try:
        from app.core.ats.services.pdf_export import generate_analysis_pdf

        pdf_bytes = generate_analysis_pdf(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {exc}") from exc
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _plain(value.model_dump())
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value
