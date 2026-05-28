from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.alumni import count_posts_by_type, list_alumni_posts
from app.core.analytics import admin_analytics_cards
from app.core.events import list_events, registration_counts
from app.core.module_catalog import MODULES
from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.supabase_client import SupabaseError, eq, rest_select
from app.core.timetable_view import latest_timetable_for_user


@dataclass(frozen=True)
class DashboardSummary:
    today_name: str
    today_timetable: list[dict]
    next_class: dict | None
    upcoming_events: list[dict]
    alumni_counts: dict[str, int]
    admin_stats: dict[str, str]
    latest_attendance: dict
    student_attendance: dict
    teacher_attendance: dict


def dashboard_summary_for_user(user: dict) -> DashboardSummary:
    today_name = datetime.now().strftime("%A")
    timetable = latest_timetable_for_user(user)
    today_entries = [entry for entry in timetable.entries if entry["day"] == today_name]
    latest_attendance = _latest_teacher_attendance(user["id"]) if user["role"] == TEACHER else {}
    return DashboardSummary(
        today_name=today_name,
        today_timetable=today_entries,
        next_class=today_entries[0] if today_entries else None,
        upcoming_events=list_events()[:5],
        alumni_counts=count_posts_by_type() if user["role"] in {STUDENT, ADMIN} else {},
        admin_stats=_admin_stats() if user["role"] == ADMIN else {},
        latest_attendance=latest_attendance,
        student_attendance=_student_attendance_summary(user["id"]) if user["role"] == STUDENT else {},
        teacher_attendance=_teacher_attendance_summary(user["id"], today_entries, latest_attendance) if user["role"] == TEACHER else {},
    )


def _admin_stats() -> dict[str, str]:
    module_total = len(MODULES)
    online_modules = sum(1 for module in MODULES.values() if module.health == "online")
    event_counts = registration_counts()
    alumni_total = sum(count_posts_by_type().values())
    return {
        "module_health": f"{online_modules}/{module_total}",
        "timetable_runs": str(_timetable_run_count()),
        "event_registrations": str(sum(event_counts.values())),
        "alumni_posts": str(alumni_total),
        "analytics_cards": str(len(admin_analytics_cards())),
    }


def _timetable_run_count() -> int:
    try:
        rows = rest_select("SchedulerApp_timetablerun", {"select": "id"})
    except SupabaseError:
        return 0
    return len(rows)


def _latest_teacher_attendance(teacher_id: str) -> dict:
    try:
        sessions = rest_select(
            "attendance_sessions",
            {
                "select": "id,subject_id,section_id,session_date,subjects(code,name),sections(name,semester,branches(code),departments(code))",
                "teacher_id": eq(teacher_id),
                "order": "session_date.desc,created_at.desc",
                "limit": "1",
            },
        )
    except SupabaseError:
        return {}
    if not sessions:
        return {}
    session = sessions[0]
    try:
        records = rest_select(
            "attendance_records",
            {
                "select": "id,status,attendance_students(roll_number,profile_id)",
                "session_id": eq(session["id"]),
            },
        )
        profiles = {str(row["id"]): row for row in rest_select("profiles", {"select": "id,full_name,email"})}
    except SupabaseError:
        records = []
        profiles = {}

    present_rows = [row for row in records if row.get("status") == "present"]
    absent_rows = [row for row in records if row.get("status") == "absent"]
    subject = session.get("subjects") or {}
    section = session.get("sections") or {}
    return {
        "session_id": str(session.get("id") or ""),
        "date": session.get("session_date") or "",
        "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or "-",
        "section": _section_label(section),
        "total": len(records),
        "present": len(present_rows),
        "absent": len(absent_rows),
        "rows": [_attendance_row(row, profiles) for row in records],
    }


def _student_attendance_summary(profile_id: str) -> dict:
    try:
        students = rest_select("attendance_students", {"select": "id", "profile_id": eq(profile_id), "limit": "1"})
    except SupabaseError:
        return {}
    if not students:
        return {"total": 0, "present": 0, "absent": 0, "percent": 0, "below_threshold": False, "recent": [], "subjects": []}
    attendance_student_id = str(students[0].get("id") or "")
    try:
        records = rest_select(
            "attendance_records",
            {
                "select": "id,status,marked_at,attendance_sessions(session_date,subjects(code,name))",
                "student_id": eq(attendance_student_id),
                "order": "marked_at.desc",
            },
        )
    except SupabaseError:
        records = []

    total = len(records)
    present = len([row for row in records if row.get("status") == "present"])
    absent = len([row for row in records if row.get("status") == "absent"])
    percent = round((present / total) * 100, 1) if total else 0
    subject_stats: dict[str, dict] = {}
    for record in records:
        session = record.get("attendance_sessions") or {}
        subject = session.get("subjects") or {}
        subject_name = f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or "Subject"
        item = subject_stats.setdefault(subject_name, {"subject": subject_name, "total": 0, "present": 0})
        item["total"] += 1
        if record.get("status") == "present":
            item["present"] += 1
    subjects = []
    for item in subject_stats.values():
        item["percent"] = round((item["present"] / item["total"]) * 100, 1) if item["total"] else 0
        item["low"] = bool(item["total"] and item["percent"] < 75)
        subjects.append(item)
    return {
        "total": total,
        "present": present,
        "absent": absent,
        "percent": percent,
        "below_threshold": bool(total and percent < 75),
        "recent": [_student_recent_record(row) for row in records[:5]],
        "subjects": sorted(subjects, key=lambda row: row["percent"])[:6],
    }


def _student_recent_record(record: dict) -> dict:
    session = record.get("attendance_sessions") or {}
    subject = session.get("subjects") or {}
    return {
        "date": session.get("session_date") or "-",
        "subject": f"{subject.get('code') or ''} {subject.get('name') or ''}".strip() or "-",
        "status": record.get("status") or "-",
    }


def _teacher_attendance_summary(teacher_id: str, today_entries: list[dict], latest_attendance: dict) -> dict:
    today = date.today().isoformat()
    try:
        sessions = rest_select(
            "attendance_sessions",
            {
                "select": "id,subject_id,section_id,session_date",
                "teacher_id": eq(teacher_id),
                "session_date": eq(today),
            },
        )
        audits = rest_select("attendance_audit_logs", {"select": "id,action,actor_id", "actor_id": eq(teacher_id)})
    except SupabaseError:
        sessions = []
        audits = []
    saved_keys = {f"{row.get('subject_id')}|{row.get('section_id')}" for row in sessions}
    pending_entries = [
        entry for entry in today_entries
        if entry.get("subject_id") and entry.get("section_id") and f"{entry.get('subject_id')}|{entry.get('section_id')}" not in saved_keys
    ]
    manual_corrections = len([row for row in audits if row.get("action") in {"manual_correction", "post_save_correction"}])
    return {
        "today_saved": len(sessions),
        "today_pending": len(pending_entries),
        "pending_entries": pending_entries[:5],
        "manual_corrections": manual_corrections,
        "latest_percent": _attendance_percent(latest_attendance),
    }


def _attendance_percent(attendance: dict) -> str:
    total = int(attendance.get("total") or 0)
    present = int(attendance.get("present") or 0)
    if not total:
        return "0%"
    return f"{round((present / total) * 100, 1)}%"


def _attendance_row(record: dict, profiles: dict[str, dict]) -> dict:
    student = record.get("attendance_students") or {}
    profile = profiles.get(str(student.get("profile_id") or ""), {})
    return {
        "roll_number": student.get("roll_number") or "-",
        "name": profile.get("full_name") or profile.get("email") or "-",
        "status": record.get("status") or "-",
    }


def _section_label(section: dict) -> str:
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
    return " / ".join(parts) or "-"
