from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.supabase_client import SupabaseError, eq, rest_select


DAY_ORDER = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}

DAY_SLOTS = (
    {"time": "09:00 - 10:00", "label": "Period 1", "is_lunch": False},
    {"time": "10:00 - 11:00", "label": "Period 2", "is_lunch": False},
    {"time": "11:00 - 12:00", "label": "Period 3", "is_lunch": False},
    {"time": "12:00 - 12:30", "label": "Lunch Break", "is_lunch": True},
    {"time": "12:30 - 13:20", "label": "Period 4", "is_lunch": False},
    {"time": "13:20 - 14:10", "label": "Period 5", "is_lunch": False},
    {"time": "14:10 - 15:00", "label": "Period 6", "is_lunch": False},
)


@dataclass(frozen=True)
class LatestTimetable:
    ok: bool
    message: str
    run: dict | None
    run_label: str
    generated_label: str
    entries: list[dict]
    sections: list[str]
    teachers: list[str]
    days: list[str]
    times: list[str]
    selected_day: str
    slot_rows: list[dict]
    section_tables: list[dict]


def latest_timetable_for_user(user: dict, day: str = "") -> LatestTimetable:
    try:
        runs = rest_select(
            "timetable_runs",
            {"select": "id,scope,generated_at,algorithm_meta", "order": "generated_at.desc,id.desc", "limit": "1"},
        )
    except SupabaseError as exc:
        return _empty(f"Could not load timetable from Supabase: {exc}")
    if not runs:
        return _empty("No platform timetable has been generated yet.")

    run = runs[0]
    entries = _entries(str(run["id"]))
    role_entries = _filter_entries(entries, user)
    sections = sorted({entry["section"] for entry in role_entries if entry["section"]})
    teachers = sorted({entry["teacher"] for entry in role_entries if entry["teacher"]})
    days = sorted({entry["day"] for entry in role_entries if entry["day"]}, key=lambda item: DAY_ORDER.get(item, 99))
    selected_day = _selected_day(day, days)
    day_entries = [entry for entry in role_entries if entry["day"] == selected_day]
    times = sorted({entry["time"] for entry in role_entries})
    message = _message_for_entries(user, role_entries, day_entries, selected_day)
    return LatestTimetable(
        ok=True,
        message=message,
        run=run,
        run_label=_run_label(run),
        generated_label=_generated_label(run),
        entries=role_entries,
        sections=sections,
        teachers=teachers,
        days=days,
        times=times,
        selected_day=selected_day,
        slot_rows=_slot_rows(day_entries),
        section_tables=_section_tables(role_entries, days),
    )


def _entries(run_id: str) -> list[dict]:
    try:
        rows = rest_select(
            "timetable_entries",
            {
                "select": "id,section_id,day,subject_id,teacher_id,room_id,time_slot_id",
                "run_id": eq(run_id),
                "order": "day.asc,section_id.asc",
            },
        )
        subjects = _by_id("subjects", "id,code,name")
        teachers = _by_id("profiles", "id,full_name,email")
        sections = _by_id("sections", "id,name,semester,academic_year,department_id,branch_id")
        departments = _by_id("departments", "id,name,code")
        branches = _by_id("branches", "id,name,code,department_id")
        rooms = _by_id("timetable_rooms", "id,room_number")
        slots = _by_id("timetable_time_slots", "id,day,start_time,end_time,label")
    except SupabaseError:
        return []

    entries = []
    for row in rows:
        section = sections.get(str(row.get("section_id")), {})
        department = departments.get(str(section.get("department_id")), {})
        branch = branches.get(str(section.get("branch_id")), {})
        subject = subjects.get(str(row.get("subject_id")), {})
        teacher = teachers.get(str(row.get("teacher_id")), {})
        room = rooms.get(str(row.get("room_id")), {})
        slot = slots.get(str(row.get("time_slot_id")), {})
        entries.append(
            {
                "id": row.get("id"),
                "section_id": str(row.get("section_id") or ""),
                "teacher_id": str(row.get("teacher_id") or ""),
                "day": row.get("day") or slot.get("day") or "",
                "time": _time_label(slot),
                "room": room.get("room_number") or "",
                "subject_code": subject.get("code") or "",
                "subject_name": subject.get("name") or "",
                "teacher": teacher.get("full_name") or teacher.get("email") or "",
                "section": _section_label(section, department, branch),
            }
        )
    entries.sort(key=lambda item: (DAY_ORDER.get(item["day"], 99), item["time"], item["section"]))
    return entries


def _filter_entries(entries: list[dict], user: dict) -> list[dict]:
    role = user.get("role")
    if role == ADMIN:
        return entries
    if role == TEACHER:
        user_id = str(user.get("id") or "")
        return [entry for entry in entries if entry["teacher_id"] == user_id]
    if role == STUDENT:
        section_id = _student_section_id(user)
        return [entry for entry in entries if section_id and entry["section_id"] == section_id]
    return []


def _student_section_id(user: dict) -> str:
    user_id = str(user.get("id") or "")
    if not user_id:
        return ""
    try:
        rows = rest_select("student_profiles", {"select": "section_id", "profile_id": eq(user_id), "limit": "1"})
    except SupabaseError:
        return ""
    return str(rows[0].get("section_id") or "") if rows else ""


def _selected_day(day: str, available_days: list[str]) -> str:
    if day in DAY_ORDER and day in available_days:
        return day
    today = datetime.now().strftime("%A")
    if today in available_days:
        return today
    return available_days[0] if available_days else today


def _no_entries_message(user: dict) -> str:
    if user.get("role") == STUDENT:
        return "No timetable found for this student. The student profile must have a section assigned."
    if user.get("role") == TEACHER:
        return "No timetable found for this teacher. Add subjects and semester/section details from My Teaching Profile, then generate again."
    return "Latest timetable exists, but no entries matched this role."


def _message_for_entries(user: dict, role_entries: list[dict], day_entries: list[dict], selected_day: str) -> str:
    if not role_entries:
        return _no_entries_message(user)
    if not day_entries:
        return f"No classes scheduled for {selected_day}."
    return ""


def _slot_rows(entries: list[dict]) -> list[dict]:
    by_time: dict[str, list[dict]] = {}
    for entry in entries:
        by_time.setdefault(entry["time"], []).append(entry)
    rows = []
    for slot in DAY_SLOTS:
        rows.append({**slot, "entries": by_time.get(slot["time"], [])})
    return rows


def _section_tables(entries: list[dict], days: list[str]) -> list[dict]:
    days = days or [day for day in DAY_ORDER if day != "Sunday"]
    sections = sorted({entry["section"] for entry in entries if entry["section"]})
    tables = []
    for section in sections:
        section_entries = [entry for entry in entries if entry["section"] == section]
        rows = []
        for day in days:
            day_entries = [entry for entry in section_entries if entry["day"] == day]
            rows.append(
                {
                    "day": day,
                    "slots": [
                        {
                            **slot,
                            "entries": [entry for entry in day_entries if entry["time"] == slot["time"]],
                        }
                        for slot in DAY_SLOTS
                    ],
                }
            )
        tables.append(
            {
                "section": section,
                "class_count": len(section_entries),
                "teacher_count": len({entry["teacher"] for entry in section_entries if entry["teacher"]}),
                "rows": rows,
            }
        )
    return tables


def _empty(message: str) -> LatestTimetable:
    return LatestTimetable(False, message, None, "", "", [], [], [], [], [], datetime.now().strftime("%A"), _slot_rows([]), [])


def _by_id(table: str, columns: str) -> dict[str, dict]:
    rows = rest_select(table, {"select": columns})
    return {str(row["id"]): row for row in rows}


def _section_label(section: dict, department: dict, branch: dict) -> str:
    parts = []
    if department.get("code"):
        parts.append(str(department["code"]))
    if branch.get("code"):
        parts.append(str(branch["code"]))
    if section.get("semester"):
        parts.append(f"Sem {section['semester']}")
    if section.get("name"):
        parts.append(str(section["name"]))
    return " / ".join(parts) or str(section.get("id") or "")


def _time_label(slot: dict) -> str:
    start = str(slot.get("start_time") or "")[:5]
    end = str(slot.get("end_time") or "")[:5]
    return f"{start} - {end}" if start and end else ""


def _run_label(run: dict) -> str:
    run_id = str(run.get("id") or "")
    return f"Run {run_id[:8]}" if run_id else "Latest run"


def _generated_label(run: dict) -> str:
    value = str(run.get("generated_at") or "")
    if not value:
        return ""
    try:
        generated = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return generated.strftime("%A, %d %b %Y, %I:%M %p")
