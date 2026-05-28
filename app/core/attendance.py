from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import os
from uuid import uuid4

from app.core.face_bridge import create_face_embedding, find_embedding_match, match_class_faces, match_face
from app.core.config import settings
from app.core.attendance_email import dispatch_attendance_emails
from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.supabase_client import (
    SupabaseError,
    admin_create_auth_user,
    eq,
    rest_insert,
    rest_select,
    rest_update,
)
from app.core.users import get_user_by_id


FACE_ENROLLMENT_DUPLICATE_THRESHOLD = 0.50
FACE_ENROLLMENT_DUPLICATE_GAP = 0.03
ATTENDANCE_REVIEW_DISTANCE = 0.48
ATTENDANCE_LOW_THRESHOLD = 75.0
ATTENDANCE_REVIEW_STATUSES = {"present", "absent", "needs_review"}
ATTENDANCE_CORRECTION_REASONS = {
    "Face missed due to blur",
    "Student present but side angle",
    "Camera issue",
}


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


def teacher_attendance_report_csv(user: dict) -> str:
    if user.get("role") != TEACHER:
        return "date,subject,section,present,total,needs_review,percent\n"
    reports = _teacher_reports(user["id"])["class_reports"]
    lines = ["date,subject,section,present,total,needs_review,percent"]
    for row in reports:
        values = [
            row.get("date", ""),
            row.get("subject", ""),
            row.get("section", ""),
            str(row.get("present", 0)),
            str(row.get("total", 0)),
            str(row.get("needs_review", 0)),
            str(row.get("percent", 0)),
        ]
        lines.append(",".join(_csv_cell(value) for value in values))
    return "\n".join(lines) + "\n"


def student_attendance_details(user: dict) -> dict:
    if user.get("role") != STUDENT:
        return {}
    context = _student_context(user)
    records = _student_record_rows(context.get("records") or [])
    return {
        **context,
        "absent": len([row for row in context.get("records", []) if row.get("status") == "absent"]),
        "needs_review": len([row for row in context.get("records", []) if row.get("status") == "needs_review"]),
        "record_rows": records,
    }


def student_attendance_report_csv(user: dict) -> str:
    context = student_attendance_details(user)
    lines = ["date,subject,status,reason,confidence,marked_at"]
    for row in context.get("record_rows", []):
        values = [
            row.get("date", ""),
            row.get("subject", ""),
            row.get("status", ""),
            row.get("reason", ""),
            str(row.get("confidence", "")),
            row.get("marked_at", ""),
        ]
        lines.append(",".join(_csv_cell(value) for value in values))
    return "\n".join(lines) + "\n"


def teacher_attendance_history(user: dict) -> dict:
    if user.get("role") != TEACHER:
        return {"sessions": [], "summary": {}}
    return _teacher_history(user["id"])


def teacher_attendance_history_csv(user: dict) -> str:
    context = teacher_attendance_history(user)
    lines = ["date,subject,section,present,absent,needs_review,total,manual_corrections,percent"]
    for row in context.get("sessions", []):
        values = [
            row.get("date", ""),
            row.get("subject", ""),
            row.get("section", ""),
            str(row.get("present", 0)),
            str(row.get("absent", 0)),
            str(row.get("needs_review", 0)),
            str(row.get("total", 0)),
            str(row.get("manual_corrections", 0)),
            str(row.get("percent", 0)),
        ]
        lines.append(",".join(_csv_cell(value) for value in values))
    return "\n".join(lines) + "\n"


def teacher_attendance_session_detail(user: dict, session_id: str) -> dict:
    if user.get("role") not in {TEACHER, ADMIN} or not session_id:
        return {}
    teacher_id = "" if user.get("role") == ADMIN else user["id"]
    context = _teacher_history(teacher_id, session_id=session_id)
    return context.get("session_detail") or {}


def teacher_attendance_session_csv(user: dict, session_id: str) -> str:
    detail = teacher_attendance_session_detail(user, session_id)
    lines = ["roll_number,student,status,reason,confidence,marked_at"]
    for row in detail.get("records", []):
        values = [
            row.get("roll_number", ""),
            row.get("name", ""),
            row.get("status", ""),
            row.get("reason", ""),
            str(row.get("confidence", "")),
            row.get("marked_at", ""),
        ]
        lines.append(",".join(_csv_cell(value) for value in values))
    return "\n".join(lines) + "\n"


def admin_attendance_analytics_context() -> dict:
    try:
        students = rest_select("attendance_students", {"select": "id,profile_id,roll_number,biometric_status"})
        profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email,role,is_active"})}
        sessions = rest_select(
            "attendance_sessions",
            {
                "select": "id,teacher_id,section_id,session_date,subjects(code,name),sections(name,semester,branches(code),departments(code))",
                "order": "session_date.desc,created_at.desc",
            },
        )
        records = rest_select("attendance_records", {"select": "id,session_id,student_id,status"})
        audits = rest_select("attendance_audit_logs", {"select": "id,record_id,action"})
    except SupabaseError:
        return {"summary": {}, "students": [], "teachers": [], "sections": []}

    records_by_student: dict[str, list[dict]] = {}
    records_by_session: dict[str, list[dict]] = {}
    for record in records:
        records_by_student.setdefault(str(record.get("student_id") or ""), []).append(record)
        records_by_session.setdefault(str(record.get("session_id") or ""), []).append(record)

    student_rows = []
    for student in students:
        profile = profiles.get(str(student.get("profile_id") or ""), {})
        stats = _status_counts(records_by_student.get(str(student.get("id")), []))
        student_rows.append(
            {
                "roll_number": student.get("roll_number") or "-",
                "name": profile.get("full_name") or profile.get("email") or "-",
                "email": profile.get("email") or "",
                "biometric_status": student.get("biometric_status") or "pending",
                **stats,
            }
        )

    teacher_rows: dict[str, dict] = {}
    section_rows: dict[str, dict] = {}
    for session in sessions:
        rows = records_by_session.get(str(session.get("id")), [])
        stats = _status_counts(rows)
        teacher = profiles.get(str(session.get("teacher_id") or ""), {})
        teacher_name = teacher.get("full_name") or teacher.get("email") or "-"
        teacher_item = teacher_rows.setdefault(
            teacher_name,
            {"teacher": teacher_name, "sessions": 0, "total": 0, "present": 0, "absent": 0, "needs_review": 0},
        )
        teacher_item["sessions"] += 1
        _merge_counts(teacher_item, stats)

        section_label = _section_display(session.get("sections") or {}) or "-"
        section_item = section_rows.setdefault(
            section_label,
            {"section": section_label, "sessions": 0, "total": 0, "present": 0, "absent": 0, "needs_review": 0},
        )
        section_item["sessions"] += 1
        _merge_counts(section_item, stats)

    manual_corrections = len([row for row in audits if row.get("action") in {"manual_correction", "post_save_correction"}])
    summary = _status_counts(records)
    summary.update(
        {
            "students": len(students),
            "verified_students": len([row for row in students if row.get("biometric_status") == "verified"]),
            "sessions": len(sessions),
            "manual_corrections": manual_corrections,
        }
    )
    return {
        "summary": summary,
        "students": sorted(student_rows, key=lambda row: row["percent"])[:100],
        "teachers": _finalize_percent_rows(teacher_rows.values(), sort_key="sessions", reverse=True),
        "sections": _finalize_percent_rows(section_rows.values(), sort_key="section"),
    }


def admin_attendance_analytics_csv() -> str:
    context = admin_attendance_analytics_context()
    lines = ["type,name,secondary,sessions,present,absent,needs_review,total,percent"]
    for row in context.get("teachers", []):
        values = ["teacher", row.get("teacher", ""), "", str(row.get("sessions", 0)), str(row.get("present", 0)), str(row.get("absent", 0)), str(row.get("needs_review", 0)), str(row.get("total", 0)), str(row.get("percent", 0))]
        lines.append(",".join(_csv_cell(value) for value in values))
    for row in context.get("sections", []):
        values = ["section", row.get("section", ""), "", str(row.get("sessions", 0)), str(row.get("present", 0)), str(row.get("absent", 0)), str(row.get("needs_review", 0)), str(row.get("total", 0)), str(row.get("percent", 0))]
        lines.append(",".join(_csv_cell(value) for value in values))
    for row in context.get("students", []):
        values = ["student", row.get("name", ""), row.get("roll_number", ""), "", str(row.get("present", 0)), str(row.get("absent", 0)), str(row.get("needs_review", 0)), str(row.get("total", 0)), str(row.get("percent", 0))]
        lines.append(",".join(_csv_cell(value) for value in values))
    return "\n".join(lines) + "\n"


def _csv_cell(value: str) -> str:
    text = str(value or "")
    return '"' + text.replace('"', '""') + '"'


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
            {"select": "student_id,status,confidence,attendance_students(roll_number,profile_id)", "session_id": eq(session_id), "order": "status.desc,marked_at.asc"},
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


def attendance_review_context(user: dict, review_token: str) -> dict:
    if not review_token or user.get("role") != TEACHER:
        return {}
    review = _read_review(review_token)
    if not review or review.get("teacher_id") != user["id"]:
        return {}
    rows = review.get("rows") or []
    return {
        **review,
        "token": review_token,
        "total_students": len(rows),
        "present": len([row for row in rows if row.get("ai_status") == "present"]),
        "absent": len([row for row in rows if row.get("ai_status") != "present"]),
        "needs_review": len([row for row in rows if row.get("ai_status") == "needs_review"]),
        "correction_reasons": sorted(ATTENDANCE_CORRECTION_REASONS),
        "summary": _review_summary(rows, review.get("total_faces") or 0),
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
        "subject_stats": _student_subject_stats(records),
        "monthly_stats": _student_monthly_stats(records),
        "below_threshold": _student_below_threshold(records),
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
    teacher_reports = _teacher_reports(user["id"])
    return {
        "title": "Attendance Classes",
        "subjects": subjects,
        "sessions": sessions,
        "classes": _teacher_timetable_classes(user),
        "class_reports": teacher_reports["class_reports"],
        "low_attendance": teacher_reports["low_attendance"],
        "manual_corrections": teacher_reports["manual_corrections"],
    }


def mark_class_attendance(
    *,
    teacher: dict,
    subject_id: str,
    section_id: str,
    image_bytes: bytes | None,
    source: str,
) -> AttendanceActionResult:
    return analyze_class_attendance(
        teacher=teacher,
        subject_id=subject_id,
        section_id=section_id,
        image_bytes_list=[image_bytes] if image_bytes else [],
        source=source,
    )


def analyze_class_attendance(
    *,
    teacher: dict,
    subject_id: str,
    section_id: str,
    image_bytes_list: list[bytes],
    source: str,
    slot_label: str = "",
    starts_at: str = "",
    ends_at: str = "",
) -> AttendanceActionResult:
    if not subject_id or not section_id:
        return AttendanceActionResult(False, "Select a timetable class first.")
    clean_images = [item for item in image_bytes_list if item]
    if not clean_images:
        return AttendanceActionResult(False, "At least one class photo is required.")
    if len(clean_images) > 4:
        return AttendanceActionResult(False, "Upload or capture up to 4 class photos at once.")

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

    merged_matches: dict[str, dict] = {}
    total_faces = 0
    image_summaries = []
    for index, image_bytes in enumerate(clean_images, start=1):
        matches, message, faces_in_photo = match_class_faces(image_bytes, roster)
        if message != "Face analysis completed.":
            return AttendanceActionResult(False, f"Photo {index}: {message}")
        total_faces += faces_in_photo
        image_summaries.append({"photo": index, "faces": faces_in_photo, "matches": len(matches)})
        for student_id, match in matches.items():
            existing = merged_matches.get(student_id)
            if existing and existing["distance"] <= match["distance"]:
                continue
            merged_matches[student_id] = {**match, "photo": index}

    rows = []
    review_distance = _get_float_env("ATTENDANCE_NEEDS_REVIEW_DISTANCE", ATTENDANCE_REVIEW_DISTANCE)
    for student in roster:
        student_id = str(student["id"])
        match = merged_matches.get(student_id)
        distance = round(float(match["distance"]), 4) if match else None
        ai_status = "absent"
        note = "No face match found."
        if match and distance is not None:
            if distance <= review_distance:
                ai_status = "present"
                note = f"Matched confidently from photo {match.get('photo')}."
            else:
                ai_status = "needs_review"
                note = f"Low-confidence match from photo {match.get('photo')}; teacher review required."
        rows.append(
            {
                "student_id": student_id,
                "profile_id": student.get("profile_id") or "",
                "name": student.get("name") or student.get("email") or student.get("roll_number") or student_id,
                "email": student.get("email") or "",
                "initials": _initials(student.get("name") or student.get("email") or student.get("roll_number") or "S"),
                "roll_number": student.get("roll_number") or "-",
                "ai_status": ai_status,
                "confidence": distance,
                "photo": match.get("photo") if match else None,
                "note": note,
            }
        )

    session_date = date.today().isoformat()
    session_starts_at = _session_timestamp(session_date, starts_at)
    session_ends_at = _session_timestamp(session_date, ends_at)
    duplicate_session = _existing_attendance_session(
        teacher["id"],
        subject_id,
        section_id,
        session_date,
        session_starts_at,
        session_ends_at,
    )
    section_label = _section_display(section)
    review_token = _write_review(
        {
            "teacher_id": teacher["id"],
            "subject_id": subject_id,
            "section_id": section_id,
            "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip(),
            "section": section_label,
            "slot_label": slot_label,
            "starts_at": session_starts_at,
            "ends_at": session_ends_at,
            "source": source,
            "session_date": session_date,
            "total_faces": total_faces,
            "total_students": len(roster),
            "image_summaries": image_summaries,
            "duplicate_session_id": duplicate_session.get("id") if duplicate_session else "",
            "duplicate_message": "Attendance already exists for this teacher, subject, section, date, and time slot." if duplicate_session else "",
            "rows": rows,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return AttendanceActionResult(
        True,
        f"AI analysis ready: {len(merged_matches)}/{len(roster)} roster students matched from {total_faces} detected face(s). Review before saving.",
        details={"review_token": review_token, "rows": rows, "duplicate_session_id": duplicate_session.get("id") if duplicate_session else ""},
    )


def save_reviewed_attendance(
    *,
    teacher: dict,
    review_token: str,
    final_statuses: dict[str, str],
    correction_reasons: dict[str, str],
    update_existing: bool,
) -> AttendanceActionResult:
    review = _read_review(review_token)
    if not review or review.get("teacher_id") != teacher["id"]:
        return AttendanceActionResult(False, "Attendance review expired. Run AI analysis again.")

    subject_id = str(review.get("subject_id") or "")
    section_id = str(review.get("section_id") or "")
    subject = _teacher_subject(teacher["id"], subject_id)
    if not subject:
        return AttendanceActionResult(False, "Selected subject is not assigned to this teacher.")

    duplicate_session_id = str(review.get("duplicate_session_id") or "")
    if duplicate_session_id and not update_existing:
        return AttendanceActionResult(False, "Attendance already exists for this class today. Choose update existing session to continue.")

    rows = review.get("rows") or []
    for row in rows:
        student_id = str(row["student_id"])
        ai_status = _clean_attendance_status(row.get("ai_status") or "absent")
        final_status = _clean_attendance_status(final_statuses.get(student_id) or ai_status)
        if final_status != ai_status and not (correction_reasons.get(student_id) or "").strip():
            correction_reasons[student_id] = "Manual Present" if final_status == "present" else "Manual Absent"

    try:
        if duplicate_session_id:
            session = rest_update("attendance_sessions", {"id": eq(duplicate_session_id)}, {"status": "closed"})[0]
        else:
            session = rest_insert(
                "attendance_sessions",
                {
                    "subject_id": subject_id,
                    "teacher_id": teacher["id"],
                    "section_id": section_id,
                    "session_date": review.get("session_date") or date.today().isoformat(),
                    "status": "closed",
                    "starts_at": review.get("starts_at") or None,
                    "ends_at": review.get("ends_at") or None,
                },
            )[0]
    except SupabaseError as exc:
        return AttendanceActionResult(False, str(exc))

    existing_records = {}
    if duplicate_session_id:
        try:
            existing_records = {
                str(row["student_id"]): row
                for row in rest_select("attendance_records", {"select": "id,student_id,status,confidence", "session_id": eq(session["id"])})
            }
        except SupabaseError:
            existing_records = {}

    results = []
    mail_records = []
    present_count = 0
    needs_review_count = 0
    manual_count = 0
    for row in rows:
        student_id = str(row["student_id"])
        ai_status = _clean_attendance_status(row.get("ai_status") or "absent")
        final_status = _clean_attendance_status(final_statuses.get(student_id) or ai_status)
        reason = (correction_reasons.get(student_id) or "").strip()
        if final_status != ai_status and not reason:
            reason = "Manual Present" if final_status == "present" else "Manual Absent"
        present_count += 1 if final_status == "present" else 0
        needs_review_count += 1 if final_status == "needs_review" else 0
        manual_count += 1 if final_status != ai_status else 0
        confidence = row.get("confidence")
        payload = {
            "session_id": session["id"],
            "student_id": student_id,
            "status": final_status,
            "confidence": confidence,
            "liveness_passed": None,
        }
        try:
            old_record = existing_records.get(student_id)
            if old_record:
                saved_record = rest_update("attendance_records", {"id": eq(old_record["id"])}, {"status": final_status, "confidence": confidence})[0]
            else:
                saved_record = rest_insert("attendance_records", payload)[0]
            _insert_attendance_audit(
                record_id=saved_record.get("id"),
                action="attendance_review_save" if final_status == ai_status else "manual_correction",
                actor_id=teacher["id"],
                old_value=old_record or {"status": ai_status},
                new_value={**payload, "ai_status": ai_status, "reason": reason, "source": review.get("source"), "photo": row.get("photo")},
            )
        except SupabaseError as exc:
            return AttendanceActionResult(False, str(exc))
        results.append(
            {
                "name": row.get("name") or row.get("email") or row.get("roll_number") or student_id,
                "roll_number": row.get("roll_number") or "-",
                "status": final_status,
                "ai_status": ai_status,
                "confidence": confidence,
                "reason": reason,
            }
        )
        mail_records.append(
            {
                "student_id": student_id,
                "name": row.get("name") or row.get("email") or row.get("roll_number") or student_id,
                "roll_number": row.get("roll_number") or "-",
                "email": row.get("email") or "",
                "status": final_status,
            }
        )

    _queue_low_attendance_audits(session["id"], teacher["id"])
    mail_result = dispatch_attendance_emails(mail_records, subject_name=review.get("subject") or "Selected Subject", marked_date=review.get("session_date"))
    _delete_review(review_token)
    details = {
        "session_id": session["id"],
        "subject": review.get("subject") or "",
        "section": review.get("section") or "",
        "slot_label": review.get("slot_label") or "",
        "source": review.get("source") or "",
        "total_faces": review.get("total_faces") or 0,
        "total_students": len(rows),
        "present": present_count,
        "absent": max(0, len(rows) - present_count - needs_review_count),
        "needs_review": needs_review_count,
        "manual_corrections": manual_count,
        "emails": mail_result,
        "results": results,
    }
    return AttendanceActionResult(
        True,
        f"Attendance marked: {present_count} present, {max(0, len(rows) - present_count - needs_review_count)} absent. {mail_result['queued']} email(s) queued.",
        details=details,
    )


def update_attendance_record_status(
    *,
    teacher: dict,
    record_id: str,
    final_status: str,
    reason: str,
) -> AttendanceActionResult:
    final_status = _clean_attendance_status(final_status)
    if not reason.strip():
        return AttendanceActionResult(False, "Correction reason is required.")
    try:
        rows = rest_select(
            "attendance_records",
            {"select": "id,status,confidence,session_id,attendance_sessions(teacher_id)", "id": eq(record_id), "limit": "1"},
        )
    except SupabaseError as exc:
        return AttendanceActionResult(False, str(exc))
    if not rows:
        return AttendanceActionResult(False, "Attendance record was not found.")
    record = rows[0]
    session = record.get("attendance_sessions") or {}
    if str(session.get("teacher_id")) != teacher["id"] and teacher.get("role") != ADMIN:
        return AttendanceActionResult(False, "You can correct only your own attendance records.")
    try:
        saved = rest_update("attendance_records", {"id": eq(record_id)}, {"status": final_status})[0]
        _insert_attendance_audit(
            record_id=record_id,
            action="post_save_correction",
            actor_id=teacher["id"],
            old_value=record,
            new_value={"status": final_status, "reason": reason.strip()},
        )
    except SupabaseError as exc:
        return AttendanceActionResult(False, str(exc))
    return AttendanceActionResult(True, "Attendance correction saved.", details={"record": saved})


def _insert_attendance_audit(record_id: str | None, action: str, actor_id: str, old_value: dict, new_value: dict) -> None:
    try:
        rest_insert(
            "attendance_audit_logs",
            {
                "record_id": record_id,
                "action": action,
                "actor_id": actor_id,
                "old_value": old_value,
                "new_value": new_value,
            },
        )
    except SupabaseError:
        # Audit failure should not lose the attendance save itself.
        return


def _queue_low_attendance_audits(session_id: str, actor_id: str) -> None:
    try:
        records = rest_select(
            "attendance_records",
            {"select": "student_id,status,attendance_students(profile_id,roll_number)", "session_id": eq(session_id)},
        )
    except SupabaseError:
        return
    for record in records:
        student = record.get("attendance_students") or {}
        attendance_student_id = str(record.get("student_id") or "")
        stats = _attendance_stats_for_student(attendance_student_id)
        if stats["total"] and stats["percent"] < ATTENDANCE_LOW_THRESHOLD:
            _insert_attendance_audit(
                None,
                "low_attendance_alert",
                actor_id,
                {},
                {
                    "attendance_student_id": attendance_student_id,
                    "profile_id": student.get("profile_id"),
                    "roll_number": student.get("roll_number"),
                    "attendance_percent": stats["percent"],
                    "total": stats["total"],
                    "present": stats["present"],
                },
            )


def _clean_attendance_status(value: str) -> str:
    status = str(value or "").strip().lower()
    if status not in ATTENDANCE_REVIEW_STATUSES:
        return "needs_review"
    return status


def _review_dir():
    path = settings.data_dir / "attendance_reviews"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _review_summary(rows: list[dict], total_faces: int) -> dict:
    present = len([row for row in rows if row.get("ai_status") == "present"])
    absent = len([row for row in rows if row.get("ai_status") != "present"])
    return {
        "matched": present,
        "unmatched": absent,
        "total_faces": total_faces,
        "match_percent": round((present / len(rows)) * 100, 1) if rows else 0,
    }


def _initials(name: str) -> str:
    parts = [part for part in str(name or "").replace("@", " ").replace(".", " ").split() if part]
    if not parts:
        return "S"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _review_path(token: str):
    safe_token = "".join(char for char in str(token) if char.isalnum() or char in {"-", "_"})
    return _review_dir() / f"{safe_token}.json"


def _write_review(payload: dict) -> str:
    token = uuid4().hex
    _review_path(token).write_text(json.dumps(payload), encoding="utf-8")
    return token


def _read_review(token: str) -> dict:
    path = _review_path(token)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _delete_review(token: str) -> None:
    path = _review_path(token)
    if path.exists():
        path.unlink()


def _existing_attendance_session(
    teacher_id: str,
    subject_id: str,
    section_id: str,
    session_date: str,
    starts_at: str = "",
    ends_at: str = "",
) -> dict:
    query = {
        "select": "id,status,created_at,starts_at,ends_at",
        "teacher_id": eq(teacher_id),
        "subject_id": eq(subject_id),
        "section_id": eq(section_id),
        "session_date": eq(session_date),
        "limit": "1",
    }
    if starts_at and ends_at:
        query["starts_at"] = eq(starts_at)
        query["ends_at"] = eq(ends_at)
    try:
        rows = rest_select("attendance_sessions", query)
    except SupabaseError:
        rows = []
    return rows[0] if rows else {}


def _session_timestamp(session_date: str, time_value: str) -> str:
    clean_time = str(time_value or "").strip()
    if not clean_time:
        return ""
    if len(clean_time) == 5:
        clean_time += ":00"
    return f"{session_date}T{clean_time}+00:00"


def _get_float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _admin_context() -> dict:
    students = rest_select("attendance_students", {"select": "id,biometric_status"})
    sessions = rest_select("attendance_sessions", {"select": "id,status"})
    records = rest_select("attendance_records", {"select": "id,status"})
    analytics = _admin_attendance_analytics()
    return {
        "title": "Attendance Overview",
        "students": len(students),
        "verified_students": len([row for row in students if row.get("biometric_status") == "verified"]),
        "sessions": len(sessions),
        "records": len(records),
        "needs_review": len([row for row in records if row.get("status") == "needs_review"]),
        "analytics": analytics,
    }


def _attendance_stats_for_student(attendance_student_id: str) -> dict:
    records = _attendance_records_for_student(attendance_student_id)
    total = len(records)
    present = len([row for row in records if row.get("status") == "present"])
    return {"total": total, "present": present, "percent": round((present / total) * 100, 1) if total else 0}


def _student_subject_stats(records: list[dict]) -> list[dict]:
    stats: dict[str, dict] = {}
    for record in records:
        session = record.get("attendance_sessions") or {}
        subject = session.get("subjects") or {}
        key = subject.get("code") or subject.get("name") or "Subject"
        item = stats.setdefault(
            key,
            {
                "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or key,
                "total": 0,
                "present": 0,
                "needs_review": 0,
            },
        )
        item["total"] += 1
        if record.get("status") == "present":
            item["present"] += 1
        if record.get("status") == "needs_review":
            item["needs_review"] += 1
    rows = []
    for item in stats.values():
        item["percent"] = round((item["present"] / item["total"]) * 100, 1) if item["total"] else 0
        item["low"] = item["percent"] < ATTENDANCE_LOW_THRESHOLD
        rows.append(item)
    return sorted(rows, key=lambda row: row["subject"])


def _student_monthly_stats(records: list[dict]) -> list[dict]:
    stats: dict[str, dict] = {}
    for record in records:
        session = record.get("attendance_sessions") or {}
        month = str(session.get("session_date") or "")[:7] or "Unknown"
        item = stats.setdefault(month, {"month": month, "total": 0, "present": 0})
        item["total"] += 1
        if record.get("status") == "present":
            item["present"] += 1
    rows = []
    for item in stats.values():
        item["percent"] = round((item["present"] / item["total"]) * 100, 1) if item["total"] else 0
        rows.append(item)
    return sorted(rows, key=lambda row: row["month"], reverse=True)


def _student_below_threshold(records: list[dict]) -> bool:
    total = len(records)
    if not total:
        return False
    present = len([row for row in records if row.get("status") == "present"])
    return ((present / total) * 100) < ATTENDANCE_LOW_THRESHOLD


def _teacher_reports(teacher_id: str) -> dict:
    try:
        sessions = rest_select(
            "attendance_sessions",
            {
                "select": "id,subject_id,section_id,session_date,subjects(code,name),sections(name,semester,branches(code),departments(code))",
                "teacher_id": eq(teacher_id),
                "order": "session_date.desc",
            },
        )
        records = rest_select(
            "attendance_records",
            {"select": "id,session_id,student_id,status,confidence,attendance_students(roll_number,profile_id)", "order": "marked_at.desc"},
        )
        profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email"})}
        audits = rest_select("attendance_audit_logs", {"select": "id,action,actor_id", "actor_id": eq(teacher_id)})
    except SupabaseError:
        return {"class_reports": [], "low_attendance": [], "manual_corrections": 0}

    session_ids = {str(row["id"]) for row in sessions}
    by_session: dict[str, list[dict]] = {str(row["id"]): [] for row in sessions}
    per_student: dict[str, dict] = {}
    for record in records:
        session_id = str(record.get("session_id") or "")
        if session_id not in session_ids:
            continue
        by_session.setdefault(session_id, []).append(record)
        student = record.get("attendance_students") or {}
        profile_id = str(student.get("profile_id") or "")
        profile = profiles.get(profile_id, {})
        item = per_student.setdefault(
            str(record.get("student_id")),
            {
                "name": profile.get("full_name") or profile.get("email") or student.get("roll_number") or "-",
                "roll_number": student.get("roll_number") or "-",
                "total": 0,
                "present": 0,
            },
        )
        item["total"] += 1
        if record.get("status") == "present":
            item["present"] += 1

    class_reports = []
    for session in sessions[:12]:
        subject = session.get("subjects") or {}
        section = session.get("sections") or {}
        rows = by_session.get(str(session["id"]), [])
        present = len([row for row in rows if row.get("status") == "present"])
        needs_review = len([row for row in rows if row.get("status") == "needs_review"])
        class_reports.append(
            {
                "date": session.get("session_date") or "-",
                "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or "-",
                "section": _section_display(section),
                "total": len(rows),
                "present": present,
                "needs_review": needs_review,
                "percent": round((present / len(rows)) * 100, 1) if rows else 0,
            }
        )

    low_attendance = []
    for item in per_student.values():
        item["percent"] = round((item["present"] / item["total"]) * 100, 1) if item["total"] else 0
        if item["total"] and item["percent"] < ATTENDANCE_LOW_THRESHOLD:
            low_attendance.append(item)
    return {
        "class_reports": class_reports,
        "low_attendance": sorted(low_attendance, key=lambda row: row["percent"])[:20],
        "manual_corrections": len([row for row in audits if row.get("action") in {"manual_correction", "post_save_correction"}]),
    }


def _admin_attendance_analytics() -> dict:
    try:
        sessions = rest_select(
            "attendance_sessions",
            {"select": "id,teacher_id,section_id,session_date,sections(name,semester,branches(code),departments(code))"},
        )
        records = rest_select("attendance_records", {"select": "id,session_id,status"})
        audits = rest_select("attendance_audit_logs", {"select": "id,action,actor_id"})
        teachers = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email"})}
    except SupabaseError:
        return {"sections": [], "teachers": [], "manual_corrections": 0, "suspicious": 0}
    records_by_session: dict[str, list[dict]] = {}
    for record in records:
        records_by_session.setdefault(str(record.get("session_id") or ""), []).append(record)

    section_stats: dict[str, dict] = {}
    teacher_stats: dict[str, dict] = {}
    for session in sessions:
        rows = records_by_session.get(str(session.get("id")), [])
        present = len([row for row in rows if row.get("status") == "present"])
        needs_review = len([row for row in rows if row.get("status") == "needs_review"])
        section_label = _section_display(session.get("sections") or {}) or "-"
        section_item = section_stats.setdefault(section_label, {"section": section_label, "sessions": 0, "total": 0, "present": 0, "needs_review": 0})
        section_item["sessions"] += 1
        section_item["total"] += len(rows)
        section_item["present"] += present
        section_item["needs_review"] += needs_review

        teacher = teachers.get(str(session.get("teacher_id") or ""), {})
        teacher_name = teacher.get("full_name") or teacher.get("email") or "-"
        teacher_item = teacher_stats.setdefault(teacher_name, {"teacher": teacher_name, "sessions": 0, "records": 0})
        teacher_item["sessions"] += 1
        teacher_item["records"] += len(rows)

    for item in section_stats.values():
        item["percent"] = round((item["present"] / item["total"]) * 100, 1) if item["total"] else 0
    return {
        "sections": sorted(section_stats.values(), key=lambda row: row["section"])[:20],
        "teachers": sorted(teacher_stats.values(), key=lambda row: row["sessions"], reverse=True)[:20],
        "manual_corrections": len([row for row in audits if row.get("action") in {"manual_correction", "post_save_correction"}]),
        "suspicious": len([row for row in records if row.get("status") == "needs_review"]),
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
        start_time = str(slot.get("start_time") or "")[:8]
        end_time = str(slot.get("end_time") or "")[:8]
        slot_label = slot.get("label") or _time_range(slot)
        classes.append(
            {
                "value": f"{entry.get('subject_id')}|{entry.get('section_id')}|{slot_label}|{start_time}|{end_time}",
                "label": f"{entry.get('day')} - {slot_label} - {subject.get('code') or ''} {subject.get('name') or ''} - {_section_display(section)}",
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


def _student_record_rows(records: list[dict]) -> list[dict]:
    reason_by_record = _audit_reasons_for_records([str(row.get("id") or "") for row in records])
    rows = []
    for record in records:
        session = record.get("attendance_sessions") or {}
        subject = session.get("subjects") or {}
        record_id = str(record.get("id") or "")
        status = record.get("status") or "-"
        rows.append(
            {
                "id": record_id,
                "date": session.get("session_date") or "-",
                "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or "-",
                "status": status,
                "reason": reason_by_record.get(record_id) or _default_attendance_reason(status),
                "confidence": record.get("confidence"),
                "marked_at": record.get("marked_at") or "",
            }
        )
    return rows


def _teacher_history(teacher_id: str, session_id: str = "") -> dict:
    try:
        session_query = {
            "select": "id,teacher_id,subject_id,section_id,session_date,starts_at,ends_at,created_at,subjects(code,name),sections(name,semester,branches(code),departments(code))",
            "order": "session_date.desc,created_at.desc",
        }
        if teacher_id:
            session_query["teacher_id"] = eq(teacher_id)
        if session_id:
            session_query["id"] = eq(session_id)
            session_query["limit"] = "1"
        sessions = rest_select("attendance_sessions", session_query)
        records = rest_select(
            "attendance_records",
            {"select": "id,session_id,student_id,status,confidence,marked_at,attendance_students(roll_number,profile_id)", "order": "marked_at.desc"},
        )
        profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email"})}
    except SupabaseError:
        return {"sessions": [], "summary": {}, "session_detail": {}}

    session_ids = {str(row.get("id") or "") for row in sessions}
    by_session: dict[str, list[dict]] = {session_id: [] for session_id in session_ids}
    relevant_record_ids = []
    for record in records:
        current_session_id = str(record.get("session_id") or "")
        if current_session_id not in session_ids:
            continue
        by_session.setdefault(current_session_id, []).append(record)
        relevant_record_ids.append(str(record.get("id") or ""))

    reason_by_record = _audit_reasons_for_records(relevant_record_ids)
    manual_by_session = _manual_corrections_by_session(by_session)
    session_rows = []
    for session in sessions:
        rows = by_session.get(str(session.get("id") or ""), [])
        stats = _status_counts(rows)
        subject = session.get("subjects") or {}
        session_rows.append(
            {
                "id": str(session.get("id") or ""),
                "date": session.get("session_date") or "-",
                "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or "-",
                "section": _section_display(session.get("sections") or {}),
                "starts_at": _time_from_timestamp(session.get("starts_at")),
                "ends_at": _time_from_timestamp(session.get("ends_at")),
                "manual_corrections": manual_by_session.get(str(session.get("id") or ""), 0),
                **stats,
            }
        )

    summary = _status_counts([record for rows in by_session.values() for record in rows])
    summary["sessions"] = len(sessions)
    summary["manual_corrections"] = sum(row["manual_corrections"] for row in session_rows)
    detail = {}
    if session_id and sessions:
        session = sessions[0]
        detail_rows = []
        for record in by_session.get(str(session.get("id") or ""), []):
            student = record.get("attendance_students") or {}
            profile = profiles.get(str(student.get("profile_id") or ""), {})
            status = record.get("status") or "-"
            detail_rows.append(
                {
                    "id": str(record.get("id") or ""),
                    "roll_number": student.get("roll_number") or "-",
                    "name": profile.get("full_name") or profile.get("email") or "-",
                    "email": profile.get("email") or "",
                    "status": status,
                    "reason": reason_by_record.get(str(record.get("id") or "")) or _default_attendance_reason(status),
                    "confidence": record.get("confidence"),
                    "marked_at": record.get("marked_at") or "",
                }
            )
        detail = {
            **session_rows[0],
            "records": detail_rows,
        }

    return {"sessions": session_rows, "summary": summary, "session_detail": detail}


def _audit_reasons_for_records(record_ids: list[str]) -> dict[str, str]:
    wanted = {record_id for record_id in record_ids if record_id}
    if not wanted:
        return {}
    try:
        audits = rest_select("attendance_audit_logs", {"select": "record_id,action,new_value,created_at", "order": "created_at.desc"})
    except SupabaseError:
        return {}
    reasons = {}
    for audit in audits:
        record_id = str(audit.get("record_id") or "")
        if record_id not in wanted or record_id in reasons:
            continue
        value = audit.get("new_value") or {}
        reason = str(value.get("reason") or "").strip()
        if reason:
            reasons[record_id] = reason
    return reasons


def _manual_corrections_by_session(records_by_session: dict[str, list[dict]]) -> dict[str, int]:
    record_to_session = {
        str(record.get("id") or ""): session_id
        for session_id, records in records_by_session.items()
        for record in records
    }
    if not record_to_session:
        return {}
    try:
        audits = rest_select("attendance_audit_logs", {"select": "record_id,action"})
    except SupabaseError:
        return {}
    counts: dict[str, int] = {}
    for audit in audits:
        if audit.get("action") not in {"manual_correction", "post_save_correction"}:
            continue
        session_id = record_to_session.get(str(audit.get("record_id") or ""))
        if session_id:
            counts[session_id] = counts.get(session_id, 0) + 1
    return counts


def _status_counts(records: list[dict]) -> dict:
    total = len(records)
    present = len([row for row in records if row.get("status") == "present"])
    absent = len([row for row in records if row.get("status") == "absent"])
    needs_review = len([row for row in records if row.get("status") == "needs_review"])
    return {
        "total": total,
        "present": present,
        "absent": absent,
        "needs_review": needs_review,
        "percent": round((present / total) * 100, 1) if total else 0,
        "low": bool(total and ((present / total) * 100) < ATTENDANCE_LOW_THRESHOLD),
    }


def _merge_counts(target: dict, stats: dict) -> None:
    for key in ("total", "present", "absent", "needs_review"):
        target[key] = int(target.get(key) or 0) + int(stats.get(key) or 0)


def _finalize_percent_rows(rows, sort_key: str, reverse: bool = False) -> list[dict]:
    finalized = []
    for row in rows:
        total = int(row.get("total") or 0)
        present = int(row.get("present") or 0)
        row["percent"] = round((present / total) * 100, 1) if total else 0
        row["low"] = bool(total and row["percent"] < ATTENDANCE_LOW_THRESHOLD)
        finalized.append(row)
    return sorted(finalized, key=lambda row: row.get(sort_key) or 0, reverse=reverse)[:100]


def _default_attendance_reason(status: str) -> str:
    if status == "absent":
        return "Absent in saved attendance."
    if status == "needs_review":
        return "Marked for teacher/admin review."
    if status == "present":
        return "Present in saved attendance."
    return "Saved attendance status."


def _time_from_timestamp(value: str | None) -> str:
    text = str(value or "")
    if "T" in text:
        return text.split("T", 1)[1][:5]
    return text[:5] if text else ""
