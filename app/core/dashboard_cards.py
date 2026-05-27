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
        DashboardCard("Resume Score", "ATS", "Check resume fit against a job description.", "/modules/ats-resume"),
        DashboardCard("Notes-to-Test", "Quiz", "Upload notes and generate practice questions.", "/modules/notes-to-test"),
        DashboardCard("Events", "Upcoming", "Track campus events and seminar updates.", "/events"),
        DashboardCard("Alumni", "Opportunities", "Find guidance, internships, and career connects.", "/alumni/opportunities"),
    ),
    TEACHER: (
        DashboardCard("Attendance Portal", "Classes", "Open attendance capture and student records.", "/attendance"),
        DashboardCard("Classroom", "Notes", "Share class notes and announcements.", "/modules/classroom"),
        DashboardCard("Notes-to-Test", "Assessments", "Generate quizzes from uploaded study material.", "/modules/notes-to-test"),
        DashboardCard("Timetable", "Today", "Review your teaching schedule.", "/timetable"),
    ),
    ADMIN: (
        DashboardCard("Users", "Manage", "Create accounts and control active access.", "/admin/users"),
        DashboardCard("Analytics", "Overview", "Review student, teacher, and module activity.", "/admin/analytics"),
        DashboardCard("Module Health", "Monitor", "Check local module URLs and launch status.", "/modules"),
        DashboardCard("Timetable", "Latest", "Review the latest generated timetable.", "/timetable"),
        DashboardCard("Events", "Manage", "Prepare events, seminars, and notices.", "/events"),
        DashboardCard("Alumni Meetups", "Plan", "Coordinate alumni meetups and opportunities.", "/modules/alumni-meetups"),
    ),
    ALUMNI: (
        DashboardCard("Jobs", "Post", "Publish internships and job opportunities.", "/alumni/opportunities"),
        DashboardCard("Guidance", "Requests", "Respond to student guidance conversations.", "/alumni/opportunities?post_type=guidance"),
        DashboardCard("Messages", "Students", "Open student connection placeholders.", "/alumni/opportunities"),
    ),
}


def cards_for_role(role: str) -> tuple[DashboardCard, ...]:
    return ROLE_DASHBOARD_CARDS.get(role, ())
