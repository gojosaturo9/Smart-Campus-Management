# LearnMate Quiz Studio Backend

FastAPI service for receiving study files, extracting chapter content, storing document data, and generating quiz questions through an LLM.

## Responsibilities

- Accept `.pdf` and `.docx` uploads.
- Accept image uploads such as `.jpg`, `.png`, `.webp`, `.tif`, and `.bmp`.
- Extract file metadata and text.
- Use OCR for photos and scanned PDF pages when Tesseract is installed.
- Detect chapter headings and split content by chapter.
- Store documents, chapters, and questions in MySQL.
- Generate quiz JSON with an OpenAI-compatible model.

## Project Structure

```text
backend/
  app/
    main.py        API routes
    models.py      SQLAlchemy ORM models
    schemas.py     Pydantic schemas
    crud.py        Database read/write helpers
    db.py          Database engine and sessions
    file_utils.py  File parsing, hashing, and metadata helpers
    llm_utils.py   LLM prompt and JSON parsing
    vectorize.py   Chapter extraction utilities
    aws_utils.py   Optional S3 helper
  ddl/             MySQL table scripts
  tests/           Pytest test suite
```

## Setup

```bash
cd backend
copy .env.example .env
pip install -r requirements.txt
```

Run the SQL files in `ddl/` against MySQL, then start the API:

For photo/scanned-PDF support, install Tesseract OCR and make sure `tesseract.exe` is available in PATH.

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
cd backend
docker-compose up --build
```

## Important Environment Variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string, for example `mysql+pymysql://user:pass@host/db`. |
| `OPENAI_API_KEY` | API key used for quiz generation. |
| `OPENAI_BASE_URL` | Optional base URL for OpenAI-compatible providers. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins allowed by CORS. |
| `UPLOAD_DIR` | Folder for uploaded source files. |

## Tests

```bash
pytest tests -v
```
