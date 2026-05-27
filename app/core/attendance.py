from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.core.face_bridge import create_face_embedding, match_face
from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.supabase_client import (
    SupabaseError,
    admin_create_auth_user,
    eq,
    rest_insert,
    rest_select,
)
from app.core.users import get_user_by_id


@dataclass(frozen=True)
class AttendanceActionResult:
    ok: bool
    message: str
    user: dict | None = None
    face_embedding: list[float] | None = None


def attendance_context(user: dict) -> dict:
    if user["role"] == STUDENT:
        return _student_context(user)
    if user["role"] == TEACHER:
        return _teacher_context(user)
    if user["role"] == ADMIN:
        return _admin_context()
    return {"title": "Attendance", "items": []}


def signup_context() -> dict:
    branch_error = ""
    try:
        branches = rest_select("branches", {"select": "id,department_id,name,code", "order": "name.asc"})
        if not branches:
            branch_error = "No branches are configured in Supabase."
    except SupabaseError as exc:
        branches = []
        branch_error = str(exc)
    return {
        "departments": rest_select("departments", {"select": "id,name,code", "order": "name.asc"}),
        "branches": branches,
        "branch_error": branch_error,
        "section_names": ["A", "B", "C", "D"],
        "semesters": list(range(1, 9)),
        "default_academic_year": "2026-27",
    }


def register_student(
    *,
    name: str,
    email: str,
    password: str,
    roll_number: str,
    department_id: str,
    branch_id: str,
    semester: str,
    section_name: str,
    academic_year: str,
    face_bytes: bytes | None,
    face_embedding: list[float] | None = None,
) -> AttendanceActionResult:
    clean_name = name.strip()
    clean_email = email.strip().lower()
    clean_roll = roll_number.strip()
    clean_section = section_name.strip().upper()
    clean_academic_year = academic_year.strip()
    semester_value = _to_int(semester)
    if not clean_name or not clean_email or not password or not clean_roll:
        return AttendanceActionResult(False, "Name, email, password, and roll number are required.")
    if not department_id or not branch_id or semester_value is None or not clean_section or not clean_academic_year:
        return AttendanceActionResult(False, "Department, branch, semester, section, and academic year are required.")
    if len(password) < 8:
        return AttendanceActionResult(False, "Password must be at least 8 characters.")
    if not face_bytes and not face_embedding:
        return AttendanceActionResult(False, "Live face scan is required to create a student attendance account.")

    if face_embedding:
        enrolled_embedding = face_embedding
    else:
        face_result = create_face_embedding(face_bytes or b"")
        if not face_result.ok or not face_result.embedding:
            return AttendanceActionResult(False, f"Face enrollment failed: {face_result.message}")
        enrolled_embedding = face_result.embedding

    try:
        section = _get_or_create_student_section(department_id, branch_id, clean_section, semester_value, clean_academic_year)
        auth_user = admin_create_auth_user(clean_email, password, clean_name, STUDENT)
        profile_id = str(auth_user["id"])
        rest_insert(
            "profiles",
            {
                "id": profile_id,
                "full_name": clean_name,
                "email": clean_email,
                "role": STUDENT,
                "is_active": True,
            },
        )
        rest_insert(
            "student_profiles",
            {
                "profile_id": profile_id,
                "roll_number": clean_roll,
                "section_id": section["id"],
            },
        )
        rest_insert(
            "attendance_students",
            {
                "profile_id": profile_id,
                "roll_number": clean_roll,
                "section_id": section["id"],
                "face_embedding": enrolled_embedding,
                "biometric_status": "verified",
            },
        )
    except (SupabaseError, KeyError) as exc:
        return AttendanceActionResult(False, str(exc))

    user = get_user_by_id(profile_id)
    return AttendanceActionResult(True, "Student account created successfully with verified face enrollment.", user)


def face_login(face_bytes: bytes | None) -> AttendanceActionResult:
    if not face_bytes:
        return AttendanceActionResult(False, "Scan your live face first.")
    try:
        students = rest_select("attendance_students", {"select": "profile_id,face_embedding,biometric_status"})
    except SupabaseError as exc:
        return AttendanceActionResult(False, str(exc))
    student, message, embedding = match_face(face_bytes, students)
    if not student:
        return AttendanceActionResult(False, message, face_embedding=embedding)
    user = get_user_by_id(str(student["profile_id"]))
    if not user or user["role"] != STUDENT:
        return AttendanceActionResult(False, "Matched face does not have an active student platform account.")
    return AttendanceActionResult(True, "Face login successful.", user)


def _student_context(user: dict) -> dict:
    profile = _student_profile(user["id"])
    attendance_student = _attendance_student(user["id"])
    records = _attendance_records_for_student(attendance_student.get("id") if attendance_student else "")
    present = sum(1 for row in records if row.get("status") == "present")
    total = len(records)
    percent = round((present / total) * 100, 1) if total else 0
    return {
        "title": "My Attendance",
        "profile": profile,
        "attendance_student": attendance_student,
        "records": records,
        "present": present,
        "total": total,
        "percent": percent,
    }


def _teacher_context(user: dict) -> dict:
    subjects = rest_select(
        "subjects",
        {"select": "id,code,name,is_active", "teacher_id": eq(user["id"]), "order": "code.asc"},
    )
    sessions = rest_select(
        "attendance_sessions",
        {"select": "id,subject_id,section_id,session_date,status", "teacher_id": eq(user["id"]), "order": "session_date.desc", "limit": "20"},
    )
    return {"title": "Attendance Classes", "subjects": subjects, "sessions": sessions}


def _admin_context() -> dict:
    students = rest_select("attendance_students", {"select": "id,biometric_status"})
    sessions = rest_select("attendance_sessions", {"select": "id,status"})
    records = rest_select("attendance_records", {"select": "id,status"})
    return {
        "title": "Attendance Overview",
        "students": len(students),
        "verified_students": len([row for row in students if row.get("biometric_status") == "verified"]),
        "sessions": len(sessions),
        "records": len(records),
    }


def _student_profile(profile_id: str) -> dict:
    rows = rest_select("student_profiles", {"select": "*, sections(name,semester,academic_year,departments(name,code),branches(name,code))", "profile_id": eq(profile_id), "limit": "1"})
    return rows[0] if rows else {}


def _attendance_student(profile_id: str) -> dict:
    rows = rest_select("attendance_students", {"select": "*", "profile_id": eq(profile_id), "limit": "1"})
    return rows[0] if rows else {}


def _attendance_records_for_student(attendance_student_id: str) -> list[dict]:
    if not attendance_student_id:
        return []
    rows = rest_select(
        "attendance_records",
        {"select": "*, attendance_sessions(session_date,status,subjects(code,name))", "student_id": eq(attendance_student_id), "order": "marked_at.desc"},
    )
    return rows


def _get_or_create_student_section(department_id: str, branch_id: str, section_name: str, semester: int, academic_year: str) -> dict:
    departments = rest_select("departments", {"select": "id", "id": eq(department_id), "limit": "1"})
    if not departments:
        raise SupabaseError("Selected department was not found.")
    branches = rest_select("branches", {"select": "id,department_id", "id": eq(branch_id), "department_id": eq(department_id), "limit": "1"})
    if not branches:
        raise SupabaseError("Selected branch was not found for this department.")

    existing = rest_select(
        "sections",
        {
            "select": "id,name,semester,academic_year,department_id,branch_id",
            "department_id": eq(department_id),
            "branch_id": eq(branch_id),
            "name": eq(section_name),
            "semester": eq(str(semester)),
            "academic_year": eq(academic_year),
            "limit": "1",
        },
    )
    if existing:
        return existing[0]
    created = rest_insert(
        "sections",
        {
            "department_id": department_id,
            "branch_id": branch_id,
            "name": section_name,
            "semester": semester,
            "academic_year": academic_year,
        },
    )
    return created[0]


def _to_int(value: str) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None
