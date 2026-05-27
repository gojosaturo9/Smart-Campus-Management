from fastapi import BackgroundTasks, FastAPI, UploadFile, File, HTTPException, Query, Depends
from pydantic import BaseModel
from app.file_utils import build_chapters_from_text, process_file, process_file_content, serialize_existing_chapters
from app.llm_utils import QuizGenerationError, generate_quiz
from app.crud import get_chapter_for_document, replace_document_chapters, save_document_and_chapters
import os
import uuid
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.db import get_db, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Document, Chapter

app = FastAPI()

class TextRevisionRequest(BaseModel):
    text: str

UPLOAD_JOBS: dict[str, dict] = {}

_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

def _document_response(status: str, document: Document, chapters: list[dict], extracted_text: str | None = None):
    return {
        "status": status,
        "book": document.title,
        "document_id": document.id,
        "chapters": chapters,
        "extracted_text": extracted_text if extracted_text is not None else "\n\n".join(
            ch.get("content", "") for ch in chapters
        ),
    }

def _save_document_payload(db: Session, document_data: dict):
    if document_data["already_exists"]:
        document = db.query(Document).filter(Document.id == document_data["document_id"]).first()
        return _document_response("existing", document, document_data["chapters"])

    doc_id = save_document_and_chapters(db, document_data)
    document = db.query(Document).filter(Document.id == doc_id).first()
    chapters = serialize_existing_chapters(document.chapters)
    return _document_response("processed", document, chapters)

def _process_upload_job(job_id: str, filename: str, content: bytes):
    UPLOAD_JOBS[job_id] = {"status": "processing", "message": "Processing material..."}
    if SessionLocal is None:
        UPLOAD_JOBS[job_id] = {
            "status": "failed",
            "error": "DATABASE_URL environment variable is not set.",
        }
        return

    db = SessionLocal()
    try:
        document_data = process_file_content(filename, content, db)
        UPLOAD_JOBS[job_id] = {"status": "completed", "result": _save_document_payload(db, document_data)}
    except (RuntimeError, ValueError, IntegrityError) as exc:
        db.rollback()
        UPLOAD_JOBS[job_id] = {"status": "failed", "error": str(exc)}
    except Exception as exc:
        db.rollback()
        UPLOAD_JOBS[job_id] = {"status": "failed", "error": "Upload processing failed."}
    finally:
        db.close()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_extensions = (".pdf", ".docx", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Upload PDF, DOCX, or an image file.")

    try:
        document_data = await process_file(file, db)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return _save_document_payload(db, document_data)
    except (ValueError, IntegrityError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/upload/background")
async def upload_file_background(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed_extensions = (".pdf", ".docx", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Upload PDF, DOCX, or an image file.")

    content = await file.read()
    job_id = str(uuid.uuid4())
    UPLOAD_JOBS[job_id] = {"status": "queued", "message": "Upload queued."}
    background_tasks.add_task(_process_upload_job, job_id, file.filename, content)
    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
async def get_upload_job(job_id: str):
    job = UPLOAD_JOBS.get(job_id)
    if not job:
        raise HTTPException(404, detail="Job not found")
    return {"job_id": job_id, **job}

@app.post("/documents/{document_id}/chapters/{chapter_id}/quiz")
async def generate_quiz_by_document_and_chapter(
    document_id: int,
    chapter_id: int,
    difficulty: str = Query("medium", pattern="^(easy|medium|hard)$"),
    question_types: str = Query("mcq"),
    db: Session = Depends(get_db),
):
    chapter = get_chapter_for_document(db, document_id, chapter_id)
    if not chapter:
        raise HTTPException(404, detail="Chapter not found for this document")

    requested_types = [item.strip().lower() for item in question_types.split(",") if item.strip()]
    try:
        return generate_quiz(chapter.id, db, difficulty=difficulty, question_types=requested_types)
    except QuizGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/generate-quiz/")
async def generate_quiz_by_book_and_chapter(
        book: str = Query(...),
        chapter_number: int = Query(...),
        difficulty: str = Query("medium", pattern="^(easy|medium|hard)$"),
        question_types: str = Query("mcq"),
        db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.title == book).first()
    if not document:
        raise HTTPException(404, detail="Book not found")

    chapters = db.query(Chapter).filter(Chapter.document_id == document.id).order_by(Chapter.id).all()
    if chapter_number < 1 or chapter_number > len(chapters):
        raise HTTPException(404, detail="Chapter not found")

    requested_types = [item.strip().lower() for item in question_types.split(",") if item.strip()]
    chapter = chapters[chapter_number - 1]
    try:
        return generate_quiz(chapter.id, db, difficulty=difficulty, question_types=requested_types)
    except QuizGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.put("/documents/{document_id}/chapters-from-text")
async def rebuild_chapters_from_text(
    document_id: int,
    payload: TextRevisionRequest,
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, detail="Document not found")

    try:
        chapters = build_chapters_from_text(payload.text, document.document_hash)
        replace_document_chapters(db, document, chapters)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved_chapters = db.query(Chapter).filter(Chapter.document_id == document.id).order_by(Chapter.id).all()
    return _document_response("revised", document, serialize_existing_chapters(saved_chapters), payload.text)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
