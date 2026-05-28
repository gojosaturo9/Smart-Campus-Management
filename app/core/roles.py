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
        NavItem("Attendance", "/attendance"),
        NavItem("Events", "/events"),
        NavItem("Timetable", "/timetable"),
        NavItem("Alumni Connect", "/alumni/opportunities"),
    ],
    TEACHER: [
        NavItem("Overview", "/teacher/dashboard"),
        NavItem("My Teaching Profile", "/teacher/setup"),
        NavItem("Attendance Portal", "/attendance"),
        NavItem("My Timetable", "/timetable"),
        NavItem("Events", "/events"),
    ],
    ADMIN: [
        NavItem("Overview", "/admin/dashboard"),
        NavItem("User Management", "/admin/users"),
        NavItem("Analytics", "/admin/analytics"),
        NavItem("Timetable", "/timetable"),
        NavItem("Events/Seminars", "/events"),
        NavItem("Alumni Posts", "/alumni/opportunities"),
    ],
    ALUMNI: [
        NavItem("Overview", "/alumni/dashboard"),
        NavItem("Student Connect", "/alumni/opportunities"),
        NavItem("Chat/Guidance", "/alumni/opportunities?post_type=guidance"),
        NavItem("Jobs/Internships", "/alumni/opportunities"),
    ],
}
