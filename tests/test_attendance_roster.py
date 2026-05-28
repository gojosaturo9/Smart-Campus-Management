from app.core import attendance


def _embedding():
    return [0.01] * 128


def test_section_roster_uses_exact_section_first(monkeypatch):
    def fake_rest_select(table, query):
        if table == "sections":
            return [
                {
                    "id": "section-a",
                    "department_id": "dept-1",
                    "branch_id": "branch-1",
                    "name": "A",
                    "semester": 3,
                    "academic_year": "2026-27",
                }
            ]
        if table == "attendance_students":
            assert query["section_id"] == "eq.section-a"
            return [
                {
                    "id": "student-1",
                    "profile_id": "profile-1",
                    "roll_number": "R001",
                    "face_embedding": _embedding(),
                    "biometric_status": "verified",
                    "section_id": "section-a",
                }
            ]
        if table == "profiles":
            return [{"id": "profile-1", "full_name": "Student One", "email": "one@example.com", "role": "student", "is_active": True}]
        return []

    monkeypatch.setattr(attendance, "rest_select", fake_rest_select)

    roster = attendance._section_roster("section-a")

    assert len(roster) == 1
    assert roster[0]["name"] == "Student One"


def test_section_roster_falls_back_to_same_class_signature(monkeypatch):
    section_calls = []

    def fake_rest_select(table, query):
        if table == "sections" and query.get("id") == "eq.timetable-section":
            return [
                {
                    "id": "timetable-section",
                    "department_id": "dept-1",
                    "branch_id": "branch-1",
                    "name": "A",
                    "semester": 3,
                    "academic_year": "2026-27",
                }
            ]
        if table == "sections" and query.get("academic_year") == "eq.2026-27":
            return [{"id": "timetable-section"}]
        if table == "sections":
            return [{"id": "signup-section"}]
        if table == "attendance_students":
            section_calls.append(query["section_id"])
            if query["section_id"] == "eq.signup-section":
                return [
                    {
                        "id": "student-1",
                        "profile_id": "profile-1",
                        "roll_number": "R001",
                        "face_embedding": _embedding(),
                        "biometric_status": "verified",
                        "section_id": "signup-section",
                    }
                ]
            return []
        if table == "profiles":
            return [{"id": "profile-1", "full_name": "Student One", "email": "one@example.com", "role": "student", "is_active": True}]
        return []

    monkeypatch.setattr(attendance, "rest_select", fake_rest_select)

    roster = attendance._section_roster("timetable-section")

    assert section_calls == ["eq.timetable-section", "eq.signup-section"]
    assert len(roster) == 1
    assert roster[0]["section_id"] == "signup-section"


def test_section_roster_ignores_unverified_and_inactive_students(monkeypatch):
    def fake_rest_select(table, query):
        if table == "sections":
            return [
                {
                    "id": "section-a",
                    "department_id": "dept-1",
                    "branch_id": "branch-1",
                    "name": "A",
                    "semester": 3,
                    "academic_year": "2026-27",
                }
            ]
        if table == "attendance_students":
            return [
                {
                    "id": "student-1",
                    "profile_id": "profile-1",
                    "roll_number": "R001",
                    "face_embedding": _embedding(),
                    "biometric_status": "pending",
                    "section_id": "section-a",
                },
                {
                    "id": "student-2",
                    "profile_id": "profile-2",
                    "roll_number": "R002",
                    "face_embedding": _embedding(),
                    "biometric_status": "verified",
                    "section_id": "section-a",
                },
            ]
        if table == "profiles":
            return [
                {"id": "profile-1", "full_name": "Student One", "email": "one@example.com", "role": "student", "is_active": True},
                {"id": "profile-2", "full_name": "Student Two", "email": "two@example.com", "role": "student", "is_active": False},
            ]
        return []

    monkeypatch.setattr(attendance, "rest_select", fake_rest_select)

    assert attendance._section_roster("section-a") == []


def test_existing_attendance_session_filters_by_time_slot(monkeypatch):
    captured = {}

    def fake_rest_select(table, query):
        captured["table"] = table
        captured["query"] = query
        return [{"id": "session-1"}]

    monkeypatch.setattr(attendance, "rest_select", fake_rest_select)

    row = attendance._existing_attendance_session(
        "teacher-1",
        "subject-1",
        "section-1",
        "2026-05-28",
        "2026-05-28T09:00:00+00:00",
        "2026-05-28T10:00:00+00:00",
    )

    assert row["id"] == "session-1"
    assert captured["table"] == "attendance_sessions"
    assert captured["query"]["starts_at"] == "eq.2026-05-28T09%3A00%3A00%2B00%3A00"
    assert captured["query"]["ends_at"] == "eq.2026-05-28T10%3A00%3A00%2B00%3A00"


def test_save_reviewed_attendance_allows_automatic_manual_note(monkeypatch):
    writes = []
    audits = []
    monkeypatch.setattr(attendance, "_read_review", lambda token: {
        "teacher_id": "teacher-1",
        "subject_id": "subject-1",
        "section_id": "section-1",
        "rows": [
            {
                "student_id": "student-1",
                "ai_status": "absent",
                "name": "Student One",
            }
        ],
    })
    monkeypatch.setattr(attendance, "_teacher_subject", lambda teacher_id, subject_id: {"id": subject_id})
    monkeypatch.setattr(attendance, "rest_insert", lambda table, row: writes.append((table, row)) or [{"id": "new-id"}])
    monkeypatch.setattr(attendance, "_insert_attendance_audit", lambda **kwargs: audits.append(kwargs))
    monkeypatch.setattr(attendance, "_queue_low_attendance_audits", lambda *args, **kwargs: None)
    monkeypatch.setattr(attendance, "dispatch_attendance_emails", lambda *args, **kwargs: {"queued": 0})
    monkeypatch.setattr(attendance, "_delete_review", lambda token: None)

    result = attendance.save_reviewed_attendance(
        teacher={"id": "teacher-1"},
        review_token="token-1",
        final_statuses={"student-1": "present"},
        correction_reasons={},
        update_existing=False,
    )

    assert result.ok
    assert result.details["manual_corrections"] == 1
    assert audits[0]["new_value"]["reason"] == "Manual Present"


def test_legacy_mark_class_attendance_only_creates_review(monkeypatch):
    saved = []

    def fake_analyze_class_attendance(**kwargs):
        return attendance.AttendanceActionResult(
            True,
            "AI analysis ready. Review before saving.",
            details={"review_token": "review-1", "rows": []},
        )

    monkeypatch.setattr(attendance, "analyze_class_attendance", fake_analyze_class_attendance)
    monkeypatch.setattr(attendance, "save_reviewed_attendance", lambda **kwargs: saved.append(kwargs))

    result = attendance.mark_class_attendance(
        teacher={"id": "teacher-1"},
        subject_id="subject-1",
        section_id="section-1",
        image_bytes=b"image",
        source="camera",
    )

    assert result.ok
    assert result.details["review_token"] == "review-1"
    assert saved == []
