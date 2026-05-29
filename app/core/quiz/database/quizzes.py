from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.supabase_client import eq, rest_delete, rest_insert, rest_select, in_


def get_document_by_hash(doc_hash: str) -> dict[str, Any] | None:
    rows = rest_select(
        "documents",
        {
            "select": "*, chapters(*)",
            "document_hash": eq(doc_hash),
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def get_document_by_id(document_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "documents",
        {
            "select": "*, chapters(*)",
            "id": eq(document_id),
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def delete_document(document_id: str, owner_id: str) -> bool:
    # Cascading delete should handle chapters and questions if set up in DB
    # If not, we do it manually. Based on schema.sql, they are 'on delete cascade'.
    deleted = rest_delete(
        "documents",
        {
            "id": eq(document_id),
            "owner_id": eq(owner_id),
        },
    )
    return bool(deleted)


def get_chapter_by_id(chapter_id: str) -> dict[str, Any] | None:
    rows = rest_select(
        "chapters",
        {
            "select": "*",
            "id": eq(chapter_id),
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def save_document_and_chapters(owner_id: str, doc_data: dict[str, Any]) -> str:
    inserted_doc = rest_insert(
        "documents",
        {
            "owner_id": owner_id,
            "title": doc_data["title"],
            "author": doc_data.get("author"),
            "file_type": doc_data.get("file_type"),
            "document_hash": doc_data["document_hash"],
            "meta": doc_data.get("meta", {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    if not inserted_doc:
        return ""
    
    doc_id = inserted_doc[0]["id"]
    
    chapter_rows = [
        {
            "document_id": doc_id,
            "chapter_title": ch["title"],
            "content": ch["content"],
            "chapter_hash": ch.get("hash") or f"{doc_data['document_hash']}:{i}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for i, ch in enumerate(doc_data["chapters"], start=1)
    ]
    rest_insert("chapters", chapter_rows)
    
    return str(doc_id)


def save_questions_for_chapter(chapter_id: str, questions: list[dict[str, Any]]) -> None:
    question_rows = [
        {
            "chapter_id": chapter_id,
            "question_text": q.get("question"),
            "answer_text": q.get("answer", ""),
            "question_type": q.get("type", "unknown"),
            "difficulty": q.get("difficulty", "medium"),
            "options": q.get("options", []),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for q in questions
    ]
    rest_insert("questions", question_rows)


def replace_document_chapters(document_id: str, chapters: list[dict[str, Any]]) -> None:
    # Delete existing chapters (cascades to questions)
    rest_delete("chapters", {"document_id": eq(document_id)})
    
    # Insert new chapters
    chapter_rows = [
        {
            "document_id": document_id,
            "chapter_title": ch["title"],
            "content": ch["content"],
            "chapter_hash": ch.get("hash"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for ch in chapters
    ]
    rest_insert("chapters", chapter_rows)
