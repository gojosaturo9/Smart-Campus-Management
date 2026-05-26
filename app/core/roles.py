from dataclasses import dataclass


STUDENT = "student"
TEACHER = "teacher"
ADMIN = "admin"
ALUMNI = "alumni"

ALL_ROLES = (STUDENT, TEACHER, ADMIN, ALUMNI)


@dataclass(frozen=True)
class NavItem:
    label: str
    endpoint: str


ROLE_HOME = {
    STUDENT: "/student/dashboard",
    TEACHER: "/teacher/dashboard",
    ADMIN: "/admin/dashboard",
    ALUMNI: "/alumni/dashboard",
}

ROLE_LABELS = {
    STUDENT: "Student",
    TEACHER: "Teacher",
    ADMIN: "Admin",
    ALUMNI: "Alumni",
}

ROLE_NAV = {
    STUDENT: [
        NavItem("Overview", "/student/dashboard"),
        NavItem("Attendance", "/modules/attendance"),
        NavItem("ATS Resume Scorer", "/modules/ats-resume"),
        NavItem("AI Notes-to-Test", "/modules/notes-to-test"),
        NavItem("Events", "/modules/events"),
        NavItem("Google Classroom", "/modules/classroom"),
        NavItem("Alumni Connect", "/modules/alumni-connect"),
        NavItem("Helpdesk/Profile", "/modules/helpdesk"),
    ],
    TEACHER: [
        NavItem("Overview", "/teacher/dashboard"),
        NavItem("Google Classroom", "/modules/classroom"),
        NavItem("Attendance Portal", "/modules/attendance"),
        NavItem("Notes-to-Test", "/modules/notes-to-test"),
        NavItem("AI Timetable", "/modules/timetable"),
    ],
    ADMIN: [
        NavItem("Overview", "/admin/dashboard"),
        NavItem("User Management", "/admin/users"),
        NavItem("Analytics", "/modules/analytics"),
        NavItem("Generate Timetable", "/modules/timetable"),
        NavItem("Events/Seminars", "/modules/events"),
        NavItem("Alumni Meetups", "/modules/alumni-meetups"),
    ],
    ALUMNI: [
        NavItem("Overview", "/alumni/dashboard"),
        NavItem("Student Connect", "/modules/alumni-connect"),
        NavItem("Chat/Guidance", "/modules/guidance"),
        NavItem("Jobs/Internships", "/modules/jobs"),
    ],
}
