from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.supabase_client import SupabaseError, rest_insert, rest_select


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

DEFAULT_PERIODS = (
    ("09:00", "10:00", "Period 1"),
    ("10:00", "11:00", "Period 2"),
    ("11:00", "12:00", "Period 3"),
    ("12:30", "13:20", "Period 4"),
    ("13:20", "14:10", "Period 5"),
    ("14:10", "15:00", "Period 6"),
)

DEFAULT_ROOMS = tuple((f"R{number}", 60) for number in range(101, 111)) + (
    ("LAB1", 40),
    ("LAB2", 40),
)


@dataclass(frozen=True)
class TimetableGenerationResult:
    ok: bool
    message: str
    run_id: str = ""
    entries: int = 0
    sections: int = 0
    teachers: int = 0
    subjects: int = 0


def generate_timetable(generated_by: str) -> TimetableGenerationResult:
    try:
        time_slots = _ensure_time_slots()
        rooms = _ensure_rooms()
        data = _load_source()
    except SupabaseError as exc:
        return TimetableGenerationResult(False, f"Could not prepare timetable data: {exc}")

    section_subjects = _section_subjects(data)
    if not section_subjects:
        return TimetableGenerationResult(
            False,
            "No teacher subjects are linked to sections. Ask teachers to re-save subject semester/section details from /teacher/setup.",
        )
    if not rooms:
        return TimetableGenerationResult(False, "No timetable rooms are available.")
    if not time_slots:
        return TimetableGenerationResult(False, "No timetable time slots are available.")

    try:
        run_row = {
            "scope": "week",
            "algorithm_meta": {
                    "source": "platform",
                    "strategy": "round_robin_conflict_aware",
                    "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    "sections": len(section_subjects),
                    "subjects": len({item["subject_id"] for items in section_subjects.values() for item in items}),
            },
        }
        if generated_by:
            run_row["generated_by"] = generated_by
        run = rest_insert("timetable_runs", run_row)[0]
    except SupabaseError as exc:
        return TimetableGenerationResult(False, f"Could not create timetable run: {exc}")

    run_id = str(run["id"])
    entries = _build_entries(run_id, section_subjects, time_slots, rooms)
    inserted = 0
    for entry in entries:
        try:
            rest_insert("timetable_entries", entry)
            inserted += 1
        except SupabaseError:
            continue

    if inserted == 0:
        return TimetableGenerationResult(False, "Timetable run was created, but no class entries could be saved.", run_id=run_id)

    teachers = {entry["teacher_id"] for entry in entries if entry.get("teacher_id")}
    subjects = {entry["subject_id"] for entry in entries if entry.get("subject_id")}
    return TimetableGenerationResult(
        True,
        f"Generated {inserted} timetable classes inside the platform.",
        run_id=run_id,
        entries=inserted,
        sections=len(section_subjects),
        teachers=len(teachers),
        subjects=len(subjects),
    )


def _load_source() -> dict[str, list[dict]]:
    return {
        "profiles": rest_select("profiles", {"select": "id,full_name,email,role,is_active"}),
        "subjects": rest_select("subjects", {"select": "id,code,name,department_id,teacher_id,is_active"}),
        "subject_sections": rest_select("subject_sections", {"select": "subject_id,section_id"}),
        "sections": rest_select("sections", {"select": "id,name,semester,academic_year,department_id,branch_id"}),
    }


def _section_subjects(data: dict[str, list[dict]]) -> dict[str, list[dict]]:
    active_teachers = {
        str(row["id"])
        for row in data["profiles"]
        if row.get("role") == "teacher" and row.get("is_active") is not False
    }
    subjects = {
        str(row["id"]): row
        for row in data["subjects"]
        if row.get("is_active") is not False and row.get("teacher_id") and str(row["teacher_id"]) in active_teachers
    }
    sections = {str(row["id"]): row for row in data["sections"]}
    grouped: dict[str, list[dict]] = {}
    for link in data["subject_sections"]:
        subject_id = str(link.get("subject_id") or "")
        section_id = str(link.get("section_id") or "")
        subject = subjects.get(subject_id)
        section = sections.get(section_id)
        if not subject or not section:
            continue
        grouped.setdefault(section_id, []).append(
            {
                "subject_id": subject_id,
                "section_id": section_id,
                "teacher_id": str(subject["teacher_id"]),
                "code": subject.get("code") or "",
            }
        )
    for section_id in grouped:
        grouped[section_id].sort(key=lambda item: item["code"])
    return grouped


def _build_entries(
    run_id: str,
    section_subjects: dict[str, list[dict]],
    time_slots: list[dict],
    rooms: list[dict],
) -> list[dict]:
    entries: list[dict] = []
    teacher_busy: set[tuple[str, str, str]] = set()
    room_busy: set[tuple[str, str, str]] = set()

    for section_index, (section_id, subjects) in enumerate(sorted(section_subjects.items())):
        cursor = section_index
        for slot in time_slots:
            day = str(slot["day"])
            slot_id = str(slot["id"])
            selected = _select_subject(subjects, cursor, teacher_busy, day, slot_id)
            if not selected:
                continue
            room = _select_room(rooms, room_busy, day, slot_id)
            if not room:
                continue
            cursor += 1
            teacher_busy.add((selected["teacher_id"], day, slot_id))
            room_busy.add((str(room["id"]), day, slot_id))
            entries.append(
                {
                    "run_id": run_id,
                    "subject_id": selected["subject_id"],
                    "section_id": section_id,
                    "teacher_id": selected["teacher_id"],
                    "room_id": str(room["id"]),
                    "time_slot_id": slot_id,
                    "day": day,
                }
            )
    return entries


def _select_subject(
    subjects: list[dict],
    cursor: int,
    teacher_busy: set[tuple[str, str, str]],
    day: str,
    slot_id: str,
) -> dict | None:
    if not subjects:
        return None
    for offset in range(len(subjects)):
        subject = subjects[(cursor + offset) % len(subjects)]
        if (subject["teacher_id"], day, slot_id) not in teacher_busy:
            return subject
    return None


def _select_room(rooms: list[dict], room_busy: set[tuple[str, str, str]], day: str, slot_id: str) -> dict | None:
    for room in rooms:
        if (str(room["id"]), day, slot_id) not in room_busy:
            return room
    return None


def _ensure_time_slots() -> list[dict]:
    rows = rest_select(
        "timetable_time_slots",
        {"select": "id,day,start_time,end_time,label", "order": "day.asc,start_time.asc"},
    )
    existing = {(row.get("day"), str(row.get("start_time"))[:5], str(row.get("end_time"))[:5]) for row in rows}
    for day in DAYS:
        for start, end, label in DEFAULT_PERIODS:
            if (day, start, end) not in existing:
                rest_insert(
                    "timetable_time_slots",
                    {"day": day, "start_time": start, "end_time": end, "label": label},
                )
    all_rows = rest_select("timetable_time_slots", {"select": "id,day,start_time,end_time,label"})
    rows = [row for row in all_rows if row.get("day") in DAYS]
    return sorted(
        rows,
        key=lambda row: (DAYS.index(row["day"]) if row.get("day") in DAYS else 99, str(row.get("start_time") or "")),
    )


def _ensure_rooms() -> list[dict]:
    rows = rest_select("timetable_rooms", {"select": "id,room_number,seating_capacity", "order": "room_number.asc"})
    if rows:
        return rows
    for room_number, capacity in DEFAULT_ROOMS:
        rest_insert("timetable_rooms", {"room_number": room_number, "seating_capacity": capacity})
    return rest_select("timetable_rooms", {"select": "id,room_number,seating_capacity", "order": "room_number.asc"})
