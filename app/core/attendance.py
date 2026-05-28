from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.core.face_bridge import create_face_embedding, find_embedding_match, match_class_faces, match_face
from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.supabase_client import (
    SupabaseError,
    admin_create_auth_user,
    eq,
    rest_insert,
    rest_select,
)
from app.core.users import get_user_by_id


FACE_ENROLLMENT_DUPLICATE_THRESHOLD = 0.50
FACE_ENROLLMENT_DUPLICATE_GAP = 0.03


@dataclass(frozen=True)
class AttendanceActionResult:
    ok: bool
    message: str
    user: dict | None = None
    face_embedding: list[float] | None = None
    details: dict | None = None


def attendance_context(user: dict) -> dict:
    if user["role"] == STUDENT:
        return _student_context(user)
    if user["role"] == TEACHER:
        return _teacher_context(user)
    if user["role"] == ADMIN:
        return _admin_context()
    return {"title": "Attendance", "items": []}


def teacher_session_result(user: dict, session_id: str) -> dict:
    if not session_id or user.get("role") != TEACHER:
        return {}
    try:
        sessions = rest_select(
            "attendance_sessions",
            {
                "select": "id,subject_id,section_id,session_date,subjects(code,name),sections(name,semester,branches(name,code),departments(name,code))",
                "id": eq(session_id),
                "teacher_id": eq(user["id"]),
                "limit": "1",
            },
        )
    except SupabaseError:
        return {}
    if not sessions:
        return {}
    try:
        records = rest_select(
            "attendance_records",
            {"select": "student_id,status,confidence,attendance_students(roll_number,profile_id)", "session_id": eq(session_id), "order": "status.desc"},
        )
        profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email"})}
    except SupabaseError:
        records = []
        profiles = {}
    rows = []
    for record in records:
        attendance_student = record.get("attendance_students") or {}
        profile = profiles.get(str(attendance_student.get("profile_id") or ""), {})
        rows.append(
            {
                "name": profile.get("full_name") or profile.get("email") or "-",
                "roll_number": attendance_student.get("roll_number") or "-",
                "status": record.get("status") or "-",
                "confidence": record.get("confidence"),
            }
        )
    session = sessions[0]
    subject = session.get("subjects") or {}
    section = session.get("sections") or {}
    return {
        "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip(),
        "section": _section_display(section),
        "date": session.get("session_date") or "",
        "present": len([row for row in rows if row["status"] == "present"]),
        "absent": len([row for row in rows if row["status"] == "absent"]),
        "rows": rows,
    }


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
    if not face_bytes:
        return AttendanceActionResult(False, "Live face scan is required to create a student attendance account.")

    face_result = create_face_embedding(face_bytes or b"")
    if not face_result.ok or not face_result.embedding:
        return AttendanceActionResult(False, f"Face enrollment failed: {face_result.message}")
    enrolled_embedding = face_result.embedding

    try:
        existing_students = rest_select("attendance_students", {"select": "profile_id,face_embedding"})
    except SupabaseError as exc:
        return AttendanceActionResult(False, str(exc))
    if find_embedding_match(
        enrolled_embedding,
        existing_students,
        threshold=FACE_ENROLLMENT_DUPLICATE_THRESHOLD,
        match_gap=FACE_ENROLLMENT_DUPLICATE_GAP,
    ):
        return AttendanceActionResult(
            False,
            "This face is already enrolled for another student. Use face login or scan the correct new student.",
        )

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
    section_id = str((profile or {}).get("section_id") or (attendance_student or {}).get("section_id") or "")
    present = sum(1 for row in records if row.get("status") == "present")
    total = len(records)
    percent = round((present / total) * 100, 1) if total else 0
    return {
        "title": "My Attendance",
        "profile": profile,
        "attendance_student": attendance_student,
        "section": profile.get("sections") or {},
        "subjects": _student_subjects(section_id),
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
        {"select": "id,subject_id,section_id,session_date,status,subjects(code,name),sections(name,semester,branches(name,code),departments(name,code))", "teacher_id": eq(user["id"]), "order": "session_date.desc", "limit": "20"},
    )
    return {"title": "Attendance Classes", "subjects": subjects, "sessions": sessions, "classes": _teacher_timetable_classes(user)}


def mark_class_attendance(
    *,
    teacher: dict,
    subject_id: str,
    section_id: str,
    image_bytes: bytes | None,
    source: str,
) -> AttendanceActionResult:
    if not image_bytes:
        return AttendanceActionResult(False, "Class photo is required.")
    if not subject_id or not section_id:
        return AttendanceActionResult(False, "Select a timetable class first.")

    subject = _teacher_subject(teacher["id"], subject_id)
    if not subject:
        return AttendanceActionResult(False, "Selected subject is not assigned to this teacher.")
    section = _section(section_id)
    if not section:
        return AttendanceActionResult(False, "Selected section was not found.")
    roster = _section_roster(section_id)
    if not roster:
        return AttendanceActionResult(
            False,
            "No enrolled students with verified face profiles were found for this section. Check student signup details: same department, branch, semester, section, and academic year.",
        )

    matches, message, total_faces = match_class_faces(image_bytes, roster)
    if message != "Face analysis completed.":
        return AttendanceActionResult(False, message)

    try:
        session = rest_insert(
            "attendance_sessions",
            {
                "subject_id": subject_id,
                "teacher_id": teacher["id"],
                "section_id": section_id,
                "session_date": date.today().isoformat(),
                "status": "closed",
            },
        )[0]
    except SupabaseError as exc:
        return AttendanceActionResult(False, str(exc))

    results = []
    present_count = 0
    for student in roster:
        student_id = str(student["id"])
        match = matches.get(student_id)
        is_present = match is not None
        present_count += 1 if is_present else 0
        confidence = round(float(match["distance"]), 4) if match else None
        try:
            rest_insert(
                "attendance_records",
                {
                    "session_id": session["id"],
                    "student_id": student_id,
                    "status": "present" if is_present else "absent",
                    "confidence": confidence,
                    "liveness_passed": True if is_present else None,
                },
            )
        except SupabaseError:
            continue
        results.append(
            {
                "name": student.get("name") or student.get("email") or student.get("roll_number") or student_id,
                "roll_number": student.get("roll_number") or "-",
                "status": "present" if is_present else "absent",
                "confidence": confidence,
            }
        )

    details = {
        "session_id": session["id"],
        "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip(),
        "section": _section_display(section),
        "source": source,
        "total_faces": total_faces,
        "total_students": len(roster),
        "present": present_count,
        "absent": max(0, len(roster) - present_count),
        "results": results,
    }
    return AttendanceActionResult(
        True,
        f"Attendance saved: {present_count}/{len(roster)} students marked present from {total_faces} detected face(s).",
        details=details,
    )


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


def _student_subjects(section_id: str) -> list[dict]:
    if not section_id:
        return []
    section_ids = _equivalent_section_ids(section_id)
    subject_ids: set[str] = set()
    for equivalent_section_id in section_ids:
        try:
            links = rest_select(
                "subject_sections",
                {"select": "subject_id", "section_id": eq(equivalent_section_id)},
            )
        except SupabaseError:
            links = []
        subject_ids.update(str(row.get("subject_id")) for row in links if row.get("subject_id"))
    if not subject_ids:
        return []
    try:
        subjects = rest_select("subjects", {"select": "id,code,name,teacher_id,is_active", "order": "code.asc"})
        profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email"})}
    except SupabaseError:
        return []
    rows = []
    for subject in subjects:
        if str(subject.get("id")) not in subject_ids:
            continue
        teacher = profiles.get(str(subject.get("teacher_id") or ""), {})
        rows.append(
            {
                "code": subject.get("code") or "-",
                "name": subject.get("name") or "-",
                "teacher": teacher.get("full_name") or teacher.get("email") or "-",
                "is_active": subject.get("is_active") is not False,
            }
        )
    return rows


def _teacher_timetable_classes(user: dict) -> list[dict]:
    try:
        runs = rest_select("timetable_runs", {"select": "id,algorithm_meta", "order": "generated_at.desc,id.desc", "limit": "50"})
    except SupabaseError:
        return []
    published_run = None
    for run in runs:
        if (run.get("algorithm_meta") or {}).get("status") == "published":
            published_run = run
            break
    if not published_run:
        return []
    try:
        entries = rest_select(
            "timetable_entries",
            {
                "select": "id,subject_id,section_id,day,subjects(code,name),sections(name,semester,academic_year,branches(name,code),departments(name,code)),timetable_time_slots(label,start_time,end_time)",
                "run_id": eq(published_run["id"]),
                "teacher_id": eq(user["id"]),
                "order": "day.asc",
            },
        )
    except SupabaseError:
        return []
    classes = []
    for entry in entries:
        subject = entry.get("subjects") or {}
        section = entry.get("sections") or {}
        slot = entry.get("timetable_time_slots") or {}
        classes.append(
            {
                "value": f"{entry.get('subject_id')}|{entry.get('section_id')}",
                "label": f"{entry.get('day')} - {slot.get('label') or _time_range(slot)} - {subject.get('code') or ''} {subject.get('name') or ''} - {_section_display(section)}",
            }
        )
    return classes


def _teacher_subject(teacher_id: str, subject_id: str) -> dict | None:
    rows = rest_select("subjects", {"select": "id,code,name,teacher_id", "id": eq(subject_id), "teacher_id": eq(teacher_id), "limit": "1"})
    return rows[0] if rows else None


def _section(section_id: str) -> dict | None:
    rows = rest_select("sections", {"select": "id,name,semester,academic_year,department_id,branch_id,branches(name,code),departments(name,code)", "id": eq(section_id), "limit": "1"})
    return rows[0] if rows else None


def _section_roster(section_id: str) -> list[dict]:
    roster = _roster_for_section_ids(_equivalent_section_ids(section_id))
    if roster:
        return roster
    return _roster_for_section_ids(_section_signature_fallback_ids(section_id))


def _roster_for_section_ids(section_ids: list[str]) -> list[dict]:
    students = []
    seen_student_ids: set[str] = set()
    for equivalent_section_id in section_ids:
        section_students = rest_select(
            "attendance_students",
            {
                "select": "id,profile_id,roll_number,face_embedding,biometric_status,section_id",
                "section_id": eq(equivalent_section_id),
            },
        )
        for student in section_students:
            student_id = str(student.get("id") or "")
            if student_id and student_id not in seen_student_ids:
                seen_student_ids.add(student_id)
                students.append(student)
    profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email,role,is_active"})}
    roster = []
    for student in students:
        if student.get("biometric_status") != "verified" or not student.get("face_embedding"):
            continue
        profile = profiles.get(str(student.get("profile_id")), {})
        if profile.get("is_active") is False:
            continue
        roster.append(
            {
                **student,
                "name": profile.get("full_name") or "",
                "email": profile.get("email") or "",
            }
        )
    return roster


def _section_signature_fallback_ids(section_id: str) -> list[str]:
    section = _section(section_id)
    if not section:
        return []
    name = str(section.get("name") or "").strip()
    semester = str(section.get("semester") or "").strip()
    department_id = str(section.get("department_id") or "").strip()
    branch_id = str(section.get("branch_id") or "").strip()
    if not name or not semester or not department_id:
        return []

    query = {
        "select": "id",
        "department_id": eq(department_id),
        "name": eq(name),
        "semester": eq(semester),
    }
    if branch_id:
        query["branch_id"] = eq(branch_id)
    try:
        rows = rest_select("sections", query)
    except SupabaseError:
        rows = []
    current_id = str(section.get("id") or section_id)
    ids = [str(row["id"]) for row in rows if row.get("id")]
    return ids or [current_id]


def _equivalent_section_ids(section_id: str) -> list[str]:
    section = _section(section_id)
    if not section:
        return [section_id] if section_id else []
    required_keys = ("department_id", "branch_id", "name", "semester", "academic_year")
    if any(section.get(key) in (None, "") for key in required_keys):
        return [str(section.get("id") or section_id)]
    try:
        rows = rest_select(
            "sections",
            {
                "select": "id",
                "department_id": eq(str(section["department_id"])),
                "branch_id": eq(str(section["branch_id"])),
                "name": eq(str(section["name"])),
                "semester": eq(str(section["semester"])),
                "academic_year": eq(str(section["academic_year"])),
            },
        )
    except SupabaseError:
        rows = []
    ids = [str(row["id"]) for row in rows if row.get("id")]
    current_id = str(section.get("id") or section_id)
    return ids or [current_id]


def _time_range(slot: dict) -> str:
    start = str(slot.get("start_time") or "")[:5]
    end = str(slot.get("end_time") or "")[:5]
    return f"{start}-{end}" if start and end else "Class"


def _section_display(section: dict) -> str:
    department = section.get("departments") or {}
    branch = section.get("branches") or {}
    parts = []
    if department.get("code"):
        parts.append(str(department["code"]))
    if branch.get("code"):
        parts.append(str(branch["code"]))
    if section.get("semester"):
        parts.append(f"Sem {section['semester']}")
    if section.get("name"):
        parts.append(f"Sec {section['name']}")
    return " / ".join(parts) or str(section.get("id") or "")


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
