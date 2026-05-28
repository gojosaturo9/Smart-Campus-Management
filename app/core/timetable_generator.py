from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import random

from app.core.supabase_client import SupabaseError, eq, rest_insert, rest_select, rest_update


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
    ("GROUND", 120),
)

MAX_TEACHER_CLASSES_PER_DAY = 4


@dataclass(frozen=True)
class TimetableGenerationResult:
    ok: bool
    message: str
    run_id: str = ""
    entries: int = 0
    sections: int = 0
    teachers: int = 0
    subjects: int = 0


def generate_timetable(generated_by: str, day: str = "") -> TimetableGenerationResult:
    selected_day = _selected_day(day)
    seed = int(datetime.utcnow().timestamp() * 1_000_000)
    rng = random.Random(seed)
    try:
        time_slots = _ensure_time_slots(selected_day)
        rooms = _ensure_rooms()
        sports_subject = _ensure_sports_subject()
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

    version = _next_version(selected_day)
    try:
        run_row = {
            "scope": "day",
            "algorithm_meta": {
                    "source": "platform",
                    "strategy": "single_day_randomized_balanced_conflict_aware",
                    "status": "draft",
                    "version": version,
                    "day": selected_day,
                    "seed": seed,
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
    entries = _build_entries(run_id, section_subjects, time_slots, rooms, sports_subject, rng)
    metrics = _generation_metrics(entries, section_subjects, time_slots)
    try:
        meta = dict(run.get("algorithm_meta") or {})
        meta["metrics"] = metrics
        rest_update("timetable_runs", {"id": eq(run_id)}, {"algorithm_meta": meta})
    except SupabaseError:
        pass
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
        f"Generated draft {version} for {selected_day} with {inserted} classes.",
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
                "name": subject.get("name") or "",
                "is_lab": _is_lab_subject(subject),
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
    sports_subject: dict,
    rng: random.Random,
) -> list[dict]:
    entries: list[dict] = []
    teacher_busy: set[tuple[str, str, str]] = set()
    room_busy: set[tuple[str, str, str]] = set()
    teacher_daily_count: dict[str, int] = {}
    teacher_last_slot_index: dict[str, int] = {}
    section_last_subject: dict[str, str] = {}
    section_subject_counts: dict[str, dict[str, int]] = {
        section_id: {subject["subject_id"]: 0 for subject in subjects}
        for section_id, subjects in section_subjects.items()
    }
    section_items = list(section_subjects.items())
    sports_assignment = _sports_assignment(section_subjects, time_slots, rng)

    for slot_index, slot in enumerate(time_slots):
        rng.shuffle(section_items)
        for section_id, subjects in section_items:
            day = str(slot["day"])
            slot_id = str(slot["id"])
            if sports_assignment == (section_id, slot_id):
                room = _sports_room(rooms, room_busy, day, slot_id, rng)
                if not room:
                    continue
                room_busy.add((str(room["id"]), day, slot_id))
                entries.append(
                    {
                        "run_id": run_id,
                        "subject_id": sports_subject["id"],
                        "section_id": section_id,
                        "teacher_id": None,
                        "room_id": str(room["id"]),
                        "time_slot_id": slot_id,
                        "day": day,
                    }
                )
                section_last_subject[section_id] = sports_subject["id"]
                continue
            selected = _select_subject(
                subjects,
                teacher_busy,
                teacher_daily_count,
                teacher_last_slot_index,
                day,
                slot_id,
                slot_index,
                rng,
                section_last_subject.get(section_id, ""),
                section_subject_counts[section_id],
            )
            if not selected:
                continue
            room = _select_room(rooms, room_busy, day, slot_id, rng, selected.get("is_lab", False))
            if not room:
                continue
            teacher_busy.add((selected["teacher_id"], day, slot_id))
            teacher_daily_count[selected["teacher_id"]] = teacher_daily_count.get(selected["teacher_id"], 0) + 1
            teacher_last_slot_index[selected["teacher_id"]] = slot_index
            room_busy.add((str(room["id"]), day, slot_id))
            section_last_subject[section_id] = selected["subject_id"]
            section_subject_counts[section_id][selected["subject_id"]] += 1
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
    teacher_busy: set[tuple[str, str, str]],
    teacher_daily_count: dict[str, int],
    teacher_last_slot_index: dict[str, int],
    day: str,
    slot_id: str,
    slot_index: int,
    rng: random.Random,
    last_subject_id: str,
    subject_counts: dict[str, int],
) -> dict | None:
    if not subjects:
        return None
    available = [
        subject
        for subject in subjects
        if (subject["teacher_id"], day, slot_id) not in teacher_busy
        and teacher_daily_count.get(subject["teacher_id"], 0) < MAX_TEACHER_CLASSES_PER_DAY
    ]
    if not available:
        return None
    not_back_to_back = [
        subject
        for subject in available
        if teacher_last_slot_index.get(subject["teacher_id"], -99) != slot_index - 1
    ]
    non_repeating = [
        subject
        for subject in (not_back_to_back or available)
        if subject["subject_id"] != last_subject_id
    ]
    candidates = non_repeating or not_back_to_back or available
    lowest_count = min(subject_counts.get(subject["subject_id"], 0) for subject in candidates)
    balanced = [subject for subject in candidates if subject_counts.get(subject["subject_id"], 0) == lowest_count]
    return rng.choice(balanced)


def _select_room(rooms: list[dict], room_busy: set[tuple[str, str, str]], day: str, slot_id: str, rng: random.Random, prefer_lab: bool = False) -> dict | None:
    available = [room for room in rooms if (str(room["id"]), day, slot_id) not in room_busy]
    if prefer_lab:
        lab_rooms = [room for room in available if "LAB" in str(room.get("room_number") or "").upper()]
        if lab_rooms:
            return rng.choice(lab_rooms)
    return rng.choice(available) if available else None


def _sports_room(rooms: list[dict], room_busy: set[tuple[str, str, str]], day: str, slot_id: str, rng: random.Random) -> dict | None:
    available = [room for room in rooms if (str(room["id"]), day, slot_id) not in room_busy]
    sports_rooms = [room for room in available if str(room.get("room_number") or "").upper() in {"GROUND", "SPORTS"}]
    return rng.choice(sports_rooms or available) if available else None


def _selected_day(day: str) -> str:
    clean_day = str(day or "").strip().title()
    if clean_day in DAYS:
        return clean_day
    today = datetime.now().strftime("%A")
    return today if today in DAYS else DAYS[0]


def _ensure_time_slots(day: str) -> list[dict]:
    rows = rest_select(
        "timetable_time_slots",
        {"select": "id,day,start_time,end_time,label", "order": "day.asc,start_time.asc"},
    )
    existing = {(row.get("day"), str(row.get("start_time"))[:5], str(row.get("end_time"))[:5]) for row in rows}
    for start, end, label in DEFAULT_PERIODS:
        if (day, start, end) not in existing:
            rest_insert(
                "timetable_time_slots",
                {"day": day, "start_time": start, "end_time": end, "label": label},
            )
    all_rows = rest_select("timetable_time_slots", {"select": "id,day,start_time,end_time,label"})
    rows = [row for row in all_rows if row.get("day") == day]
    return sorted(
        rows,
        key=lambda row: str(row.get("start_time") or ""),
    )


def _ensure_rooms() -> list[dict]:
    rows = rest_select("timetable_rooms", {"select": "id,room_number,seating_capacity", "order": "room_number.asc"})
    if rows:
        return rows
    for room_number, capacity in DEFAULT_ROOMS:
        rest_insert("timetable_rooms", {"room_number": room_number, "seating_capacity": capacity})
    return rest_select("timetable_rooms", {"select": "id,room_number,seating_capacity", "order": "room_number.asc"})


def _ensure_sports_subject() -> dict:
    rows = rest_select("subjects", {"select": "*", "code": eq("SPORTS"), "limit": "1"})
    if rows:
        return rows[0]
    return rest_insert(
        "subjects",
        {
            "code": "SPORTS",
            "name": "Sports",
            "teacher_id": None,
            "department_id": None,
            "is_active": True,
        },
    )[0]


def _next_version(day: str) -> int:
    runs = rest_select("timetable_runs", {"select": "algorithm_meta", "order": "generated_at.desc", "limit": "100"})
    versions = []
    for run in runs:
        meta = run.get("algorithm_meta") or {}
        if meta.get("day") == day:
            try:
                versions.append(int(meta.get("version") or 0))
            except (TypeError, ValueError):
                continue
    return max(versions or [0]) + 1


def publish_timetable(run_id: str) -> TimetableGenerationResult:
    runs = rest_select("timetable_runs", {"select": "id,algorithm_meta", "id": eq(run_id), "limit": "1"})
    if not runs:
        return TimetableGenerationResult(False, "Timetable draft was not found.")
    run = runs[0]
    meta = dict(run.get("algorithm_meta") or {})
    day = meta.get("day") or ""
    existing_runs = rest_select("timetable_runs", {"select": "id,algorithm_meta", "order": "generated_at.desc", "limit": "100"})
    for existing in existing_runs:
        existing_meta = dict(existing.get("algorithm_meta") or {})
        if existing_meta.get("day") == day and existing_meta.get("status") == "published":
            existing_meta["status"] = "archived"
            rest_update("timetable_runs", {"id": eq(existing["id"])}, {"algorithm_meta": existing_meta})
    meta["status"] = "published"
    meta["published_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    rest_update("timetable_runs", {"id": eq(run_id)}, {"algorithm_meta": meta})
    return TimetableGenerationResult(True, "Timetable published for teachers and students.", run_id=run_id)


def _sports_assignment(section_subjects: dict[str, list[dict]], time_slots: list[dict], rng: random.Random) -> tuple[str, str] | None:
    if not section_subjects or not time_slots:
        return None
    section_id = rng.choice(list(section_subjects.keys()))
    slot = rng.choice(time_slots)
    return section_id, str(slot["id"])


def _is_lab_subject(subject: dict) -> bool:
    text = f"{subject.get('code') or ''} {subject.get('name') or ''}".lower()
    return any(marker in text for marker in ("lab", "practical", "workshop"))


def _generation_metrics(entries: list[dict], section_subjects: dict[str, list[dict]], time_slots: list[dict]) -> dict:
    teacher_keys = [(entry.get("teacher_id"), entry["day"], entry["time_slot_id"]) for entry in entries if entry.get("teacher_id")]
    room_keys = [(entry.get("room_id"), entry["day"], entry["time_slot_id"]) for entry in entries if entry.get("room_id")]
    expected_slots = len(section_subjects) * len(time_slots)
    sports_count = sum(1 for entry in entries if str(entry.get("subject_id") or "") and entry.get("teacher_id") is None)
    return {
        "teacher_conflicts": len(teacher_keys) - len(set(teacher_keys)),
        "room_conflicts": len(room_keys) - len(set(room_keys)),
        "free_periods": max(0, expected_slots - len(entries)),
        "sports_classes": sports_count,
        "teacher_max_daily_classes": MAX_TEACHER_CLASSES_PER_DAY,
    }
