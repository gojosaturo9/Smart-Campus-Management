from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status, Query
from fastapi.responses import RedirectResponse, Response

from app.auth.session import require_role
from app.core.quiz.database.quizzes import (
    delete_document,
    get_document_by_id,
    save_document_and_chapters,
    get_chapter_by_id,
)
from app.core.quiz.services.file_utils import process_file_content, build_chapters_from_text
from app.core.quiz.services.llm_utils import generate_quiz_for_chapter, QuizGenerationError
from app.core.roles import STUDENT, TEACHER
from app.core.templates import templates

router = APIRouter(prefix="/quiz")


@router.get("")
def quiz_home(request: Request, user: dict = Depends(require_role(STUDENT))):
    return templates.TemplateResponse(
        "quiz/index.html",
        {
            "request": request,
            "user": user,
            "error": request.query_params.get("error", ""),
            "success": request.query_params.get("success", ""),
        },
    )


@router.post("/upload")
async def upload_material(
    request: Request,
    material: UploadFile = File(...),
    user: dict = Depends(require_role(STUDENT)),
):
    filename = material.filename or "material"
    file_bytes = await material.read()

    try:
        doc_data = process_file_content(filename, file_bytes)
        if doc_data.get("already_exists"):
            doc_id = doc_data["document_id"]
        else:
            doc_id = save_document_and_chapters(user["id"], doc_data)
    except Exception as exc:
        return RedirectResponse(
            url=f"/quiz?error=Upload failed: {exc}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=f"/quiz/chapters/{doc_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/chapters/{doc_id}")
def view_chapters(
    doc_id: str,
    request: Request,
    user: dict = Depends(require_role(STUDENT)),
):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return templates.TemplateResponse(
        "quiz/chapters.html",
        {
            "request": request,
            "user": user,
            "doc": doc,
            "chapters": doc.get("chapters", []),
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/chapters/{chapter_id}/generate")
async def generate_quiz(
    request: Request,
    chapter_id: str,
    difficulty: str = Form("medium"),
    question_types: str = Form("mcq"),
    user: dict = Depends(require_role(STUDENT)),
):
    requested_types = [t.strip() for t in question_types.split(",") if t.strip()]
    try:
        result = generate_quiz_for_chapter(chapter_id, difficulty=difficulty, question_types=requested_types)
        if "error" in result:
             raise ValueError(result["error"])
    except QuizGenerationError as exc:
        chapter = get_chapter_by_id(chapter_id)
        doc_id = chapter["document_id"] if chapter else ""
        return RedirectResponse(
            url=f"/quiz/chapters/{doc_id}?error={exc}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as exc:
        chapter = get_chapter_by_id(chapter_id)
        doc_id = chapter["document_id"] if chapter else ""
        return RedirectResponse(
            url=f"/quiz/chapters/{doc_id}?error=Quiz generation failed: {exc}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        "quiz/attempt.html",
        {
            "request": request,
            "user": user,
            "quiz": result,
            "chapter_id": chapter_id,
        },
    )

# For AJAX requests from the attempt page
@router.post("/api/chapters/{chapter_id}/quiz")
async def api_generate_quiz(
    chapter_id: str,
    difficulty: str = Query("medium"),
    question_types: str = Query("mcq"),
    user: dict = Depends(require_role(STUDENT)),
):
    requested_types = [t.strip() for t in question_types.split(",") if t.strip()]
    try:
        return generate_quiz_for_chapter(chapter_id, difficulty=difficulty, question_types=requested_types)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
