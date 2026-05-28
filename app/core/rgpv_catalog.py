from __future__ import annotations


DEPARTMENTS = (
    {"code": "CSE", "name": "Computer Science and Engineering"},
    {"code": "ECE", "name": "Electronics and Communication Engineering"},
    {"code": "ME", "name": "Mechanical Engineering"},
    {"code": "CE", "name": "Civil Engineering"},
    {"code": "EE", "name": "Electrical Engineering"},
)

BRANCHES = (
    {"code": "CSE", "name": "Computer Science and Engineering", "department_code": "CSE"},
    {"code": "IT", "name": "Information Technology", "department_code": "CSE"},
    {"code": "AIML", "name": "Artificial Intelligence and Machine Learning", "department_code": "CSE"},
    {"code": "ECE", "name": "Electronics and Communication Engineering", "department_code": "ECE"},
    {"code": "ME", "name": "Mechanical Engineering", "department_code": "ME"},
    {"code": "CE", "name": "Civil Engineering", "department_code": "CE"},
    {"code": "EE", "name": "Electrical Engineering", "department_code": "EE"},
)

SUBJECTS = (
    {"code": "BT-101", "name": "Engineering Chemistry", "branch_code": "ALL", "semester": 1},
    {"code": "BT-102", "name": "Mathematics-I", "branch_code": "ALL", "semester": 1},
    {"code": "BT-103", "name": "English for Communication", "branch_code": "ALL", "semester": 1},
    {"code": "BT-104", "name": "Basic Electrical and Electronics Engineering", "branch_code": "ALL", "semester": 1},
    {"code": "BT-105", "name": "Engineering Graphics", "branch_code": "ALL", "semester": 1},
    {"code": "BT-201", "name": "Engineering Physics", "branch_code": "ALL", "semester": 2},
    {"code": "BT-202", "name": "Mathematics-II", "branch_code": "ALL", "semester": 2},
    {"code": "BT-203", "name": "Basic Mechanical Engineering", "branch_code": "ALL", "semester": 2},
    {"code": "BT-204", "name": "Basic Civil Engineering and Mechanics", "branch_code": "ALL", "semester": 2},
    {"code": "BT-205", "name": "Basic Computer Engineering", "branch_code": "ALL", "semester": 2},
    {"code": "CS-301", "name": "Energy and Environmental Engineering", "branch_code": "CSE", "semester": 3},
    {"code": "CS-302", "name": "Discrete Structure", "branch_code": "CSE", "semester": 3},
    {"code": "CS-303", "name": "Data Structure", "branch_code": "CSE", "semester": 3},
    {"code": "CS-304", "name": "Digital Systems", "branch_code": "CSE", "semester": 3},
    {"code": "CS-305", "name": "Object Oriented Programming", "branch_code": "CSE", "semester": 3},
    {"code": "CS-401", "name": "Mathematics-III", "branch_code": "CSE", "semester": 4},
    {"code": "CS-402", "name": "Analysis and Design of Algorithm", "branch_code": "CSE", "semester": 4},
    {"code": "CS-403", "name": "Software Engineering", "branch_code": "CSE", "semester": 4},
    {"code": "CS-404", "name": "Computer Organization and Architecture", "branch_code": "CSE", "semester": 4},
    {"code": "CS-405", "name": "Operating Systems", "branch_code": "CSE", "semester": 4},
    {"code": "CS-501", "name": "Theory of Computation", "branch_code": "CSE", "semester": 5},
    {"code": "CS-502", "name": "Database Management Systems", "branch_code": "CSE", "semester": 5},
    {"code": "CS-503", "name": "Data Analytics", "branch_code": "CSE", "semester": 5},
    {"code": "CS-504", "name": "Internet and Web Technology", "branch_code": "CSE", "semester": 5},
    {"code": "CS-601", "name": "Machine Learning", "branch_code": "CSE", "semester": 6},
    {"code": "CS-602", "name": "Computer Networks", "branch_code": "CSE", "semester": 6},
    {"code": "CS-603", "name": "Compiler Design", "branch_code": "CSE", "semester": 6},
    {"code": "CS-604", "name": "Project Management", "branch_code": "CSE", "semester": 6},
    {"code": "IT-301", "name": "Data Structure", "branch_code": "IT", "semester": 3},
    {"code": "IT-302", "name": "Digital Systems", "branch_code": "IT", "semester": 3},
    {"code": "IT-401", "name": "Operating Systems", "branch_code": "IT", "semester": 4},
    {"code": "IT-402", "name": "Software Engineering", "branch_code": "IT", "semester": 4},
    {"code": "IT-501", "name": "Database Management Systems", "branch_code": "IT", "semester": 5},
    {"code": "IT-502", "name": "Computer Networks", "branch_code": "IT", "semester": 5},
    {"code": "IT-601", "name": "Cloud Computing", "branch_code": "IT", "semester": 6},
    {"code": "IT-602", "name": "Information Security", "branch_code": "IT", "semester": 6},
    {"code": "AI-301", "name": "Data Structures", "branch_code": "AIML", "semester": 3},
    {"code": "AI-302", "name": "Python Programming", "branch_code": "AIML", "semester": 3},
    {"code": "AI-401", "name": "Artificial Intelligence", "branch_code": "AIML", "semester": 4},
    {"code": "AI-402", "name": "Database Management Systems", "branch_code": "AIML", "semester": 4},
    {"code": "AI-501", "name": "Machine Learning", "branch_code": "AIML", "semester": 5},
    {"code": "AI-502", "name": "Data Mining and Warehousing", "branch_code": "AIML", "semester": 5},
    {"code": "AI-601", "name": "Deep Learning", "branch_code": "AIML", "semester": 6},
    {"code": "AI-602", "name": "Natural Language Processing", "branch_code": "AIML", "semester": 6},
    {"code": "EC-301", "name": "Electronic Devices", "branch_code": "ECE", "semester": 3},
    {"code": "EC-302", "name": "Digital Circuits and Systems", "branch_code": "ECE", "semester": 3},
    {"code": "EC-401", "name": "Analog Communication", "branch_code": "ECE", "semester": 4},
    {"code": "EC-402", "name": "Microprocessors and Microcontrollers", "branch_code": "ECE", "semester": 4},
    {"code": "EC-501", "name": "Digital Communication", "branch_code": "ECE", "semester": 5},
    {"code": "EC-502", "name": "Control Systems", "branch_code": "ECE", "semester": 5},
    {"code": "ME-301", "name": "Thermodynamics", "branch_code": "ME", "semester": 3},
    {"code": "ME-302", "name": "Strength of Materials", "branch_code": "ME", "semester": 3},
    {"code": "ME-401", "name": "Fluid Mechanics", "branch_code": "ME", "semester": 4},
    {"code": "ME-402", "name": "Theory of Machines", "branch_code": "ME", "semester": 4},
    {"code": "CE-301", "name": "Building Materials and Construction", "branch_code": "CE", "semester": 3},
    {"code": "CE-302", "name": "Surveying", "branch_code": "CE", "semester": 3},
    {"code": "CE-401", "name": "Structural Analysis", "branch_code": "CE", "semester": 4},
    {"code": "CE-402", "name": "Geotechnical Engineering", "branch_code": "CE", "semester": 4},
    {"code": "EE-301", "name": "Electrical Machines-I", "branch_code": "EE", "semester": 3},
    {"code": "EE-302", "name": "Network Analysis", "branch_code": "EE", "semester": 3},
    {"code": "EE-401", "name": "Electrical Machines-II", "branch_code": "EE", "semester": 4},
    {"code": "EE-402", "name": "Power System-I", "branch_code": "EE", "semester": 4},
)


def academic_years(start_year: int = 2026, count: int = 4) -> list[str]:
    return [f"{year}-{str(year + 1)[-2:]}" for year in range(start_year, start_year + count)]


def subject_by_code(code: str) -> dict | None:
    clean_code = str(code or "").strip().upper()
    for subject in SUBJECTS:
        if subject["code"] == clean_code:
            return dict(subject)
    return None


def department_by_code(code: str) -> dict | None:
    clean_code = str(code or "").strip().upper()
    for department in DEPARTMENTS:
        if department["code"] == clean_code:
            return dict(department)
    return None


def branch_by_code(code: str) -> dict | None:
    clean_code = str(code or "").strip().upper()
    for branch in BRANCHES:
        if branch["code"] == clean_code:
            return dict(branch)
    return None
