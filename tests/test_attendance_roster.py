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
