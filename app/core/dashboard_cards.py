from dataclasses import dataclass

from app.core.roles import ADMIN, ALUMNI, STUDENT, TEACHER


@dataclass(frozen=True)
class DashboardCard:
    title: str
    value: str
    description: str
    href: str


ROLE_DASHBOARD_CARDS = {
    STUDENT: (
        DashboardCard("Attendance", "Status", "Open your attendance portal and review subject records.", "/attendance"),
        DashboardCard("Timetable", "Today", "Review your latest class schedule.", "/timetable"),
        DashboardCard("Events", "Upcoming", "Track campus events and seminar updates.", "/events"),
        DashboardCard("Alumni", "Opportunities", "Find guidance, internships, and career connects.", "/alumni/opportunities"),
    ),
    TEACHER: (
        DashboardCard("Attendance Portal", "Classes", "Open attendance capture and student records.", "/attendance"),
        DashboardCard("Timetable", "Today", "Review your teaching schedule.", "/timetable"),
        DashboardCard("Events", "Campus", "Review upcoming campus events and seminars.", "/events"),
    ),
    ADMIN: (
        DashboardCard("Users", "Manage", "Create accounts and control active access.", "/admin/users"),
        DashboardCard("Analytics", "Overview", "Review student, teacher, and platform activity.", "/admin/analytics"),
        DashboardCard("Timetable", "Latest", "Review the latest generated timetable.", "/timetable"),
        DashboardCard("Events", "Manage", "Prepare events, seminars, and notices.", "/events"),
        DashboardCard("Alumni Posts", "Review", "Review alumni jobs, internships, and guidance posts.", "/alumni/opportunities"),
    ),
    ALUMNI: (
        DashboardCard("Jobs", "Post", "Publish internships and job opportunities.", "/alumni/opportunities"),
        DashboardCard("Guidance", "Requests", "Respond to student guidance conversations.", "/alumni/opportunities?post_type=guidance"),
        DashboardCard("Messages", "Students", "Open student connection placeholders.", "/alumni/opportunities"),
    ),
}


def cards_for_role(role: str) -> tuple[DashboardCard, ...]:
    return ROLE_DASHBOARD_CARDS.get(role, ())
