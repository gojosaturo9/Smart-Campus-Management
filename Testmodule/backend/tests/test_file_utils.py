"""Unit tests for app.file_utils"""
import hashlib
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.file_utils import (
    hash_content,
    extract_title_from_filename,
    save_file,
    extract_text_from_docx,
    process_file_content,
    split_into_chapters,
    split_into_study_sections,
)


# ---------------------------------------------------------------------------
# hash_content
# ---------------------------------------------------------------------------

def test_hash_content_bytes():
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    assert hash_content(data) == expected


def test_hash_content_str():
    data = "hello world"
    expected = hashlib.sha256(data.encode("utf-8")).hexdigest()
    assert hash_content(data) == expected


def test_hash_content_is_deterministic():
    assert hash_content(b"abc") == hash_content(b"abc")


def test_hash_content_differs_for_different_inputs():
    assert hash_content(b"abc") != hash_content(b"xyz")


# ---------------------------------------------------------------------------
# extract_title_from_filename
# ---------------------------------------------------------------------------

def test_extract_title_simple():
    assert extract_title_from_filename("biology_textbook.pdf") == "biology textbook"


def test_extract_title_with_hyphens():
    assert extract_title_from_filename("intro-to-python.docx") == "intro to python"


def test_extract_title_strips_extension():
    title = extract_title_from_filename("my_document.pdf")
    assert ".pdf" not in title


def test_extract_title_empty_name():
    # os.path.splitext("") -> ("", "") then strip -> ""
    # Fallback should return "Unknown Title"
    result = extract_title_from_filename("")
    assert result == "Unknown Title"


def test_extract_title_path_included():
    result = extract_title_from_filename("/some/path/my_file.pdf")
    assert result == "my file"


# ---------------------------------------------------------------------------
# split_into_chapters
# ---------------------------------------------------------------------------

def test_split_into_chapters_basic():
    text = "Chapter 1\nSome content.\nChapter 2\nMore content."
    chapters = split_into_chapters(text)
    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter 1"
    assert chapters[1]["title"] == "Chapter 2"


def test_split_into_chapters_unit():
    text = "Unit I\nContent A.\nUnit II\nContent B."
    chapters = split_into_chapters(text)
    assert len(chapters) == 2


def test_split_into_chapters_empty():
    assert split_into_chapters("No sections here.") == []


def test_split_into_chapters_case_insensitive():
    text = "chapter 1\nstuff\nCHAPTER 2\nmore stuff"
    chapters = split_into_chapters(text)
    assert len(chapters) == 2


def test_split_into_study_sections_creates_fallback_sections():
    text = " ".join(f"word{i}" for i in range(10))
    sections = split_into_study_sections(text, words_per_section=4)
    assert len(sections) == 3
    assert sections[0]["title"] == "Study Section 1"
    assert sections[0]["content"] == "word0 word1 word2 word3"


def test_split_into_study_sections_empty_text():
    assert split_into_study_sections("") == []


# ---------------------------------------------------------------------------
# save_file
# ---------------------------------------------------------------------------

def test_save_file(tmp_path, monkeypatch):
    import app.file_utils as fu
    monkeypatch.setattr(fu, "UPLOAD_DIR", str(tmp_path))
    save_file("abc123", "pdf", b"pdf content")
    saved = tmp_path / "abc123.pdf"
    assert saved.exists()
    assert saved.read_bytes() == b"pdf content"


def test_process_file_content_rejects_large_upload(monkeypatch):
    import app.file_utils as fu
    monkeypatch.setattr(fu, "MAX_UPLOAD_BYTES", 4)
    with pytest.raises(ValueError, match="too large"):
        process_file_content("notes.pdf", b"12345", MagicMock())
