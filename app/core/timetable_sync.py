from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product

from app.core.config import settings
from app.core.supabase_client import SupabaseError, eq, rest_delete, rest_insert, rest_select, rest_update


@dataclass(frozen=True)
class TimetableSyncResult:
    ok: bool
    message: str
    teachers: int = 0
    subjects: int = 0
    departments: int = 0
    sections: int = 0
    students: int = 0


def sync_attendance_to_timetable() -> TimetableSyncResult:
    attendance_url, attendance_key = _attendance_supabase_config()
    if not attendance_url or not attendance_key:
        return TimetableSyncResult(False, "Platform Supabase secrets are not configured.")

    try:
        source = _platform_native_source()
        if not source:
            return TimetableSyncResult(False, "No active teacher subjects found in canonical platform tables.")
        teachers = source["teachers"]
        subjects = source["subjects"]
        students = source["students"]

        teacher_ids = _sync_teachers(teachers)
        course_ids = _sync_courses(subjects, students)
        dept_ids, section_count = _sync_departments_sections(subjects, course_ids)
        _sync_course_instructors(subjects, teacher_ids, course_ids)
        _sync_ai_subjects(subjects, teacher_ids, course_ids)
        student_count = _sync_students(students, dept_ids)
    except SupabaseError as exc:
        return TimetableSyncResult(False, f"Supabase timetable sync failed: {exc}")

    return TimetableSyncResult(
        True,
        "Teacher subjects synced to Supabase timetable data.",
        teachers=len(teacher_ids),
        subjects=len(course_ids),
        departments=len(dept_ids),
        sections=section_count,
        students=student_count,
    )


def _sync_teachers(teachers: list[dict]) -> dict[str, int]:
    teacher_ids: dict[str, int] = {}
    for teacher in teachers:
        source_id = str(teacher.get("teacher_id") or teacher.get("username") or "")
        if not source_id:
            continue
        uid = _short_code(teacher.get("username") or source_id, 6)
        name = str(teacher.get("name") or teacher.get("username") or "Teacher")[:25]
        row = _first("SchedulerApp_instructor", {"select": "id", "uid": eq(uid), "limit": "1"})
        if row:
            instructor_id = int(row["id"])
            rest_update("SchedulerApp_instructor", {"id": eq(instructor_id)}, {"name": name})
        else:
            created = rest_insert("SchedulerApp_instructor", {"uid": uid, "name": name})
            instructor_id = int(created[0]["id"])
        teacher_ids[source_id] = instructor_id
    return teacher_ids


def _sync_courses(subjects: list[dict], students: list[dict]) -> dict[str, str]:
    student_count_by_class = _student_count_by_class(students)
    course_ids: dict[str, str] = {}
    for subject in subjects:
        source_id = _subject_source_id(subject)
        if not source_id:
            continue
        course_number = _short_code(subject.get("subject_code") or subject.get("code") or source_id, 12)
        payload = {
            "course_number": course_number,
            "course_name": str(subject.get("name") or subject.get("subject_name") or subject.get("subject_code") or "Subject")[:40],
            "max_numb_students": str(_estimate_subject_students(subject, student_count_by_class)),
        }
        if _first("SchedulerApp_course", {"select": "course_number", "course_number": eq(course_number), "limit": "1"}):
            rest_update("SchedulerApp_course", {"course_number": eq(course_number)}, payload)
        else:
            rest_insert("SchedulerApp_course", payload)
        course_ids[source_id] = course_number
    return course_ids


def _sync_departments_sections(subjects: list[dict], course_ids: dict[str, str]) -> tuple[dict[str, int], int]:
    dept_ids: dict[str, int] = {}
    section_count = 0
    for subject in subjects:
        source_id = str(subject.get("subject_id") or subject.get("subject_code") or "")
        course_id = course_ids.get(source_id)
        if not course_id:
            continue
        for dept_name, section_id in _target_classes(subject):
            dept_id = _get_or_create_department(dept_name)
            dept_ids[dept_name] = dept_id
            _link("SchedulerApp_department_courses", "department_id", dept_id, "course_id", course_id)
            payload = {
                "section_id": section_id,
                "department_id": dept_id,
                "num_class_in_week": 30,
                "course_id": None,
            }
            if _first("SchedulerApp_section", {"select": "section_id", "section_id": eq(section_id), "limit": "1"}):
                rest_update("SchedulerApp_section", {"section_id": eq(section_id)}, payload)
            else:
                rest_insert("SchedulerApp_section", payload)
            section_count += 1
    return dept_ids, section_count


def _sync_course_instructors(
    subjects: list[dict],
    teacher_ids: dict[str, int],
    course_ids: dict[str, str],
) -> None:
    for subject in subjects:
        instructor_id = teacher_ids.get(str(subject.get("teacher_id") or ""))
        course_id = course_ids.get(_subject_source_id(subject))
        if instructor_id and course_id:
            _unlink_course_instructors(course_id)
            _link("SchedulerApp_course_instructors", "course_id", course_id, "instructor_id", instructor_id)


def _sync_ai_subjects(
    subjects: list[dict],
    teacher_ids: dict[str, int],
    course_ids: dict[str, str],
) -> None:
    for subject in subjects:
        instructor_id = teacher_ids.get(str(subject.get("teacher_id") or ""))
        course_id = course_ids.get(_subject_source_id(subject))
        if not instructor_id or not course_id:
            continue
        subject_name = str(subject.get("name") or subject.get("subject_name") or subject.get("subject_code") or "Subject")[:80]
        max_students = int(subject.get("max_students") or 60)
        for _, section_id in _target_classes(subject):
            subject_code = _subject_code(course_id, section_id)
            payload = {
                "subject_code": subject_code,
                "subject_name": subject_name,
                "teacher_id": instructor_id,
                "section_id": section_id,
                "weekly_classes": 5,
                "max_students": max_students,
                "is_active": True,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            if _first("SchedulerApp_aisubject", {"select": "id", "subject_code": eq(subject_code), "limit": "1"}):
                payload.pop("created_at", None)
                rest_update("SchedulerApp_aisubject", {"subject_code": eq(subject_code)}, payload)
            else:
                rest_insert("SchedulerApp_aisubject", payload)


def _sync_students(students: list[dict], dept_ids: dict[str, int]) -> int:
    count = 0
    for student in students:
        roll = str(student.get("enrollment_no") or student.get("student_id") or "")[:30]
        if not roll:
            continue
        dept_name, section_id = _student_class(student)
        if dept_name not in dept_ids:
            dept_ids[dept_name] = _get_or_create_department(dept_name)
            if not _first("SchedulerApp_section", {"select": "section_id", "section_id": eq(section_id), "limit": "1"}):
                rest_insert(
                    "SchedulerApp_section",
                    {"section_id": section_id, "department_id": dept_ids[dept_name], "num_class_in_week": 30},
                )
        payload = {
            "roll_number": roll,
            "name": str(student.get("name") or "Student")[:80],
            "email": str(student.get("email_id") or ""),
            "section_id": section_id,
            "is_active": True,
        }
        if _first("SchedulerApp_student", {"select": "id", "roll_number": eq(roll), "limit": "1"}):
            rest_update("SchedulerApp_student", {"roll_number": eq(roll)}, payload)
        else:
            rest_insert("SchedulerApp_student", payload)
        count += 1
    return count


def _get_or_create_department(dept_name: str) -> int:
    row = _first("SchedulerApp_department", {"select": "id", "dept_name": eq(dept_name), "limit": "1"})
    if row:
        return int(row["id"])
    created = rest_insert("SchedulerApp_department", {"dept_name": dept_name})
    return int(created[0]["id"])


def _link(table: str, left_key: str, left_value: object, right_key: str, right_value: object) -> None:
    query = {
        "select": "id",
        left_key: eq(str(left_value)),
        right_key: eq(str(right_value)),
        "limit": "1",
    }
    if _first(table, query):
        return
    rest_insert(table, {left_key: left_value, right_key: right_value})


def _unlink_course_instructors(course_id: str) -> None:
    rows = rest_select("SchedulerApp_course_instructors", {"select": "id", "course_id": eq(course_id)})
    for row in rows:
        rest_delete("SchedulerApp_course_instructors", {"id": eq(row["id"])})


def _first(table: str, query: dict[str, str]) -> dict | None:
    rows = rest_select(table, query)
    return rows[0] if rows else None


def _platform_native_source() -> dict[str, list[dict]] | None:
    profiles = rest_select("profiles", {"select": "*"})
    teacher_profiles = [row for row in profiles if row.get("role") == "teacher" and row.get("is_active")]
    if not teacher_profiles:
        return None

    departments = {row["id"]: row for row in rest_select("departments", {"select": "*"})}
    branches = {row["id"]: row for row in rest_select("branches", {"select": "*"})}
    sections = rest_select("sections", {"select": "*"})
    section_by_id = {row["id"]: row for row in sections}
    section_ids_by_subject: dict[str, list[str]] = {}
    for row in rest_select("subject_sections", {"select": "*"}):
        section_ids_by_subject.setdefault(row["subject_id"], []).append(row["section_id"])

    teacher_ids = {str(row["id"]) for row in teacher_profiles}
    subjects = []
    for subject in rest_select("subjects", {"select": "*"}):
        teacher_id = str(subject.get("teacher_id") or "")
        if teacher_id not in teacher_ids or subject.get("is_active") is False:
            continue

        department = departments.get(subject.get("department_id"), {})
        target_sections = [
            section_by_id[section_id]
            for section_id in section_ids_by_subject.get(subject.get("id"), [])
            if section_id in section_by_id
        ]
        if not target_sections:
            continue
        target_branch = _branch_label(branches.get(target_sections[0].get("branch_id"), {}), department)
        subjects.append(
            {
                "subject_id": str(subject.get("id") or subject.get("code") or ""),
                "subject_code": subject.get("code") or "",
                "name": subject.get("name") or subject.get("code") or "Subject",
                "teacher_id": teacher_id,
                "max_students": subject.get("max_students") or 60,
                "target_branch": target_branch,
                "target_classes": [
                    {
                        "branch": _branch_label(branches.get(section.get("branch_id"), {}), department),
                        "semester": section.get("semester") or "",
                        "section": section.get("name") or "A",
                    }
                    for section in target_sections
                ],
            }
        )

    if not subjects:
        return None

    students = _platform_students(profiles, departments)
    teachers = [
        {
            "teacher_id": str(row["id"]),
            "username": row.get("email", "").split("@")[0],
            "name": row.get("full_name") or row.get("email") or "Teacher",
        }
        for row in teacher_profiles
    ]
    return {"teachers": teachers, "subjects": subjects, "students": students}


def _platform_students(profiles: list[dict], departments: dict[str, dict]) -> list[dict]:
    profile_by_id = {str(row["id"]): row for row in profiles}
    sections = {row["id"]: row for row in rest_select("sections", {"select": "*"})}
    branches = {row["id"]: row for row in rest_select("branches", {"select": "*"})}
    students = []
    for student_profile in rest_select("student_profiles", {"select": "*"}):
        profile = profile_by_id.get(str(student_profile.get("profile_id")))
        if not profile:
            continue
        section = sections.get(student_profile.get("section_id"), {})
        department = departments.get(section.get("department_id"), {})
        branch = branches.get(section.get("branch_id"), {})
        students.append(
            {
                "student_id": str(profile.get("id")),
                "enrollment_no": student_profile.get("roll_number") or profile.get("email"),
                "name": profile.get("full_name") or profile.get("email") or "Student",
                "email_id": profile.get("email") or "",
                "branch": _branch_label(branch, department),
                "semester": section.get("semester") or "",
                "section": section.get("name") or "A",
            }
        )
    return students


def _branch_label(branch: dict, department: dict) -> str:
    return branch.get("code") or branch.get("name") or department.get("code") or department.get("name") or "General"


def _subject_source_id(subject: dict) -> str:
    return str(subject.get("subject_id") or subject.get("id") or subject.get("subject_code") or subject.get("code") or "")


def _target_classes(subject: dict) -> list[tuple[str, str]]:
    if subject.get("target_classes"):
        return [
            (
                _dept_name(item.get("branch") or "General", item.get("semester") or ""),
                _section_id(item.get("branch") or "General", item.get("semester") or "", item.get("section") or "A"),
            )
            for item in subject["target_classes"]
        ]
    branches = _values(subject.get("target_branch")) or ["General"]
    semesters = _values(subject.get("target_semester")) or [""]
    sections = _values(subject.get("target_section")) or ["A"]
    return [(_dept_name(branch, semester), _section_id(branch, semester, section)) for branch, semester, section in product(branches, semesters, sections)]


def _student_class(student: dict) -> tuple[str, str]:
    return _dept_name(student.get("branch") or "General", student.get("semester") or ""), _section_id(
        student.get("branch") or "General",
        student.get("semester") or "",
        student.get("section") or "A",
    )


def _student_count_by_class(students: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for student in students:
        _, section_id = _student_class(student)
        counts[section_id] = counts.get(section_id, 0) + 1
    return counts


def _estimate_subject_students(subject: dict, counts: dict[str, int]) -> int:
    return max(sum(counts.get(section_id, 0) for _, section_id in _target_classes(subject)), 1)


def _dept_name(branch: object, semester: object) -> str:
    branch_text = str(branch or "General").strip().upper()
    semester_text = str(semester or "").strip()
    return f"{branch_text} Sem {semester_text}"[:50] if semester_text else branch_text[:50]


def _section_id(branch: object, semester: object, section: object) -> str:
    value = "-".join(
        part
        for part in (
            str(branch or "General").strip().upper(),
            str(semester or "").strip(),
            str(section or "A").strip().upper(),
        )
        if part
    )
    return _short_code(value, 25)


def _values(value: object) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    return [value]


def _short_code(value: object, max_length: int) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "", str(value or "")).upper()
    return (text or "X")[:max_length]


def _subject_code(course_id: str, section_id: str) -> str:
    base = _short_code(course_id, 20)
    existing = _first("SchedulerApp_aisubject", {"select": "section_id", "subject_code": eq(base), "limit": "1"})
    if not existing or existing.get("section_id") == section_id:
        return base
    return f"{base}{_short_code(section_id, 20)}"[:20]


def _attendance_supabase_config() -> tuple[str, str]:
    return settings.supabase_url, settings.supabase_service_role_key


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
