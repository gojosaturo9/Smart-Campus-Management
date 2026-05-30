from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass(frozen=True)
class ModuleInfo:
    key: str
    name: str
    description: str
    relative_path: str
    stack: str
    entry_hint: str
    allowed_roles: tuple[str, ...]
    url_env_key: str = ""

    @property
    def path(self) -> Path:
        return settings.workspace_dir / self.relative_path

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def launch_url(self) -> str:
        return settings.env(self.url_env_key) if self.url_env_key else ""

    @property
    def health(self) -> str:
        if not self.launch_url:
            return "not configured"
        try:
            request = Request(self.launch_url, headers={"User-Agent": "SmartCampusHealth/1.0"})
            with urlopen(request, timeout=1.5) as response:
                return "online" if response.status < 500 else "error"
        except (OSError, URLError, ValueError):
            return "offline"


MODULES = {
    "attendance": ModuleInfo(
        key="attendance",
        name="AI Attendance System",
        description="Biometric and face-recognition attendance module.",
        relative_path="TruePresence/AI-powered-attendance-platform",
        stack="Streamlit + Python AI",
        entry_hint="streamlit run app.py",
        allowed_roles=("student", "teacher", "admin"),
        url_env_key="ATTENDANCE_URL",
    ),
    "timetable": ModuleInfo(
        key="timetable",
        name="AI Timetable Generator",
        description="Genetic-algorithm timetable scheduler.",
        relative_path="AItimetable",
        stack="Django",
        entry_hint="python manage.py runserver",
        allowed_roles=("teacher", "admin"),
        url_env_key="TIMETABLE_URL",
    ),
    "ats-resume": ModuleInfo(
        key="ats-resume",
        name="AI ATS Resume Scorer",
        description="Resume scoring and job-description matching.",
        relative_path="resume ats",
        stack="FastAPI + Streamlit",
        entry_hint="uvicorn backend.main:app + streamlit frontend",
        allowed_roles=("student",),
        url_env_key="ATS_FRONTEND_URL",
    ),
    "notes-to-test": ModuleInfo(
        key="notes-to-test",
        name="AI Notes-to-Test Generator",
        description="Study-material upload and quiz generation module.",
        relative_path="Testmodule",
        stack="FastAPI + frontend",
        entry_hint="Run backend and frontend from module README",
        allowed_roles=("student", "teacher"),
        url_env_key="NOTES_TEST_URL",
    ),
    "alumni-connect": ModuleInfo(
        key="alumni-connect",
        name="Alumni Connection",
        description="Student-alumni guidance and networking area.",
        relative_path="alumini",
        stack="Pending integration",
        entry_hint="To be connected in a later phase",
        allowed_roles=("student", "admin", "alumni"),
        url_env_key="ALUMNI_URL",
    ),
}


PLACEHOLDER_MODULES = {
    "events": ("Events", ("student", "admin")),
    "classroom": ("Google Classroom", ("student", "teacher")),
    "helpdesk": ("Helpdesk/Profile", ("student",)),
    "teacher-accounts": ("Teacher Account Management", ("admin",)),
    "analytics": ("Analytics", ("admin",)),
    "alumni-meetups": ("Alumni Meetups", ("admin",)),
    "guidance": ("Chat/Guidance", ("alumni",)),
    "jobs": ("Jobs/Internships", ("alumni",)),
}


def list_modules_for_role(role: str) -> list[ModuleInfo]:
    return [module for module in MODULES.values() if role in module.allowed_roles]
