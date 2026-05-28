from __future__ import annotations

import re

from app.core.rgpv_catalog import BRANCHES, DEPARTMENTS, SUBJECTS, academic_years, branch_by_code, department_by_code, subject_by_code
from app.core.supabase_client import SupabaseError, eq, rest_insert, rest_select, rest_update


def teacher_setup_context(user: dict) -> dict:
    departments = rest_select("departments", {"select": "*", "order": "name.asc"})
    branches = rest_select("branches", {"select": "*", "order": "name.asc"})
    sections = rest_select("sections", {"select": "*", "order": "name.asc"})
    subjects = rest_select("subjects", {"select": "*", "teacher_id": eq(user["id"]), "order": "code.asc"})
    teacher_profile = _teacher_profile(user["id"]) or {}
    department_by_id = {row["id"]: row for row in departments}
    branch_by_id = {row["id"]: row for row in branches}
    section_by_id = {row["id"]: row for row in sections}
    subject_sections = rest_select("subject_sections", {"select": "*"})
    section_links_by_subject: dict[str, list[dict]] = {}
    for link in subject_sections:
        section = section_by_id.get(link.get("section_id"))
        if section:
            section_links_by_subject.setdefault(link.get("subject_id"), []).append(section)

    return {
        "teacher_profile": teacher_profile,
        "departments": departments,
        "branches": branches,
        "sections": sections,
        "catalog_departments": DEPARTMENTS,
        "catalog_branches": BRANCHES,
        "catalog_subjects": SUBJECTS,
        "academic_years": academic_years(),
        "semesters": list(range(1, 9)),
        "section_names": ["A", "B", "C", "D"],
        "subjects": [
            {
                **subject,
                "department_name": department_by_id.get(subject.get("department_id"), {}).get("name", ""),
                "linked_sections": [
                    {
                        **section,
                        "branch_name": branch_by_id.get(section.get("branch_id"), {}).get("name", ""),
                        "branch_code": branch_by_id.get(section.get("branch_id"), {}).get("code", ""),
                    }
                    for section in section_links_by_subject.get(subject.get("id"), [])
                ],
            }
            for subject in subjects
        ],
    }


def save_teacher_profile(user: dict, employee_code: str, designation: str) -> tuple[bool, str]:
    payload = {
        "profile_id": user["id"],
        "employee_code": employee_code.strip() or None,
        "designation": designation.strip() or None,
    }
    try:
        existing = _teacher_profile(user["id"])
        if existing:
            rest_update("teacher_profiles", {"profile_id": eq(user["id"])}, payload)
        else:
            rest_insert("teacher_profiles", payload)
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Teacher profile saved."


def save_teacher_subject(
    user: dict,
    subject_code: str,
    subject_name: str,
    department_name: str,
    department_code: str,
    branch_name: str,
    branch_code: str,
    semester: str,
    section_name: str,
    academic_year: str,
) -> tuple[bool, str]:
    clean_subject_code = _code(subject_code, 24)
    catalog_subject = subject_by_code(clean_subject_code)
    clean_subject_name = (catalog_subject or {}).get("name") or subject_name.strip()
    clean_department_code = _code(department_code or department_name, 16)
    clean_branch_code = _code(branch_code or branch_name, 16)
    catalog_department = department_by_code(clean_department_code)
    catalog_branch = branch_by_code(clean_branch_code)
    clean_department_name = (catalog_department or {}).get("name") or department_name.strip()
    clean_branch_name = (catalog_branch or {}).get("name") or branch_name.strip()
    clean_section_name = (section_name.strip() or "A").upper()
    clean_academic_year = academic_year.strip() or "2026-27"
    semester_value = _to_int(semester)

    if not clean_subject_code or not clean_subject_name or not clean_department_name or not clean_branch_name or semester_value is None:
        return False, "Subject code, subject name, department, branch, and semester are required."

    try:
        department = _get_or_create_department(clean_department_name, clean_department_code)
        branch = _get_or_create_branch(department["id"], clean_branch_name, clean_branch_code)
        section = _get_or_create_section(department["id"], branch["id"], clean_section_name, semester_value, clean_academic_year)
        subject = _subject_by_code(clean_subject_code)
        payload = {
            "code": clean_subject_code,
            "name": clean_subject_name,
            "department_id": department["id"],
            "teacher_id": user["id"],
            "is_active": True,
        }
        if subject:
            if subject.get("teacher_id") and subject.get("teacher_id") != user["id"]:
                return False, f"{clean_subject_code} is already assigned to another teacher."
            saved_subject = rest_update("subjects", {"code": eq(clean_subject_code)}, payload)[0]
        else:
            saved_subject = rest_insert("subjects", payload)[0]
        _link_subject_section(saved_subject["id"], section["id"])
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Subject saved for timetable generation."


def _teacher_profile(profile_id: str) -> dict | None:
    rows = rest_select("teacher_profiles", {"select": "*", "profile_id": eq(profile_id), "limit": "1"})
    return rows[0] if rows else None


def _get_or_create_department(name: str, code: str) -> dict:
    rows = rest_select("departments", {"select": "*", "code": eq(code), "limit": "1"})
    if rows:
        rest_update("departments", {"id": eq(rows[0]["id"])}, {"name": name, "code": code})
        rows[0].update({"name": name, "code": code})
        return rows[0]
    created = rest_insert("departments", {"name": name, "code": code})
    return created[0]


def _get_or_create_branch(department_id: str, name: str, code: str) -> dict:
    rows = rest_select("branches", {"select": "*", "department_id": eq(department_id), "code": eq(code), "limit": "1"})
    if rows:
        rest_update("branches", {"id": eq(rows[0]["id"])}, {"department_id": department_id, "name": name, "code": code})
        rows[0].update({"department_id": department_id, "name": name, "code": code})
        return rows[0]
    created = rest_insert("branches", {"department_id": department_id, "name": name, "code": code})
    return created[0]


def _get_or_create_section(department_id: str, branch_id: str, name: str, semester: int, academic_year: str) -> dict:
    candidates = rest_select(
        "sections",
        {
            "select": "*",
            "department_id": eq(department_id),
            "branch_id": eq(branch_id),
            "name": eq(name),
            "semester": eq(str(semester)),
            "academic_year": eq(academic_year),
            "limit": "1",
        },
    )
    if candidates:
        return candidates[0]
    created = rest_insert(
        "sections",
        {
            "department_id": department_id,
            "branch_id": branch_id,
            "name": name,
            "semester": semester,
            "academic_year": academic_year,
        },
    )
    return created[0]


def _subject_by_code(code: str) -> dict | None:
    rows = rest_select("subjects", {"select": "*", "code": eq(code), "limit": "1"})
    return rows[0] if rows else None


def _link_subject_section(subject_id: str, section_id: str) -> None:
    existing = rest_select(
        "subject_sections",
        {
            "select": "id",
            "subject_id": eq(subject_id),
            "section_id": eq(section_id),
            "limit": "1",
        },
    )
    if not existing:
        rest_insert("subject_sections", {"subject_id": subject_id, "section_id": section_id})


def _code(value: str, max_length: int) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value or "").upper()[:max_length]


def _to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
