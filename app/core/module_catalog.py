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
    api_url_env_key: str = ""
    api_health_path: str = ""
    command_env_key: str = ""
    api_command_env_key: str = ""
    platform_url: str = ""

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
    def api_url(self) -> str:
        return settings.env(self.api_url_env_key) if self.api_url_env_key else ""

    @property
    def start_command(self) -> str:
        return settings.env(self.command_env_key) if self.command_env_key else ""

    @property
    def api_start_command(self) -> str:
        return settings.env(self.api_command_env_key) if self.api_command_env_key else ""

    @property
    def preferred_url(self) -> str:
        return self.platform_url or self.launch_url

    @property
    def dashboard_url(self) -> str:
        return self.platform_url or f"/modules/{self.key}"

    @property
    def health(self) -> str:
        return self.health_for_url(self.launch_url)

    @property
    def api_health(self) -> str:
        if not self.api_url:
            return "not configured"
        return self.health_for_url(self.api_url.rstrip("/") + self.api_health_path)

    @staticmethod
    def health_for_url(url: str) -> str:
        if not url:
            return "not configured"
        try:
            request = Request(url, headers={"User-Agent": "SmartCampusHealth/1.0"})
            with urlopen(request, timeout=0.35) as response:
                return "online" if response.status < 500 else "error"
        except (OSError, URLError, ValueError):
            return "offline"


MODULES = {
    "attendance": ModuleInfo(
        key="attendance",
        name="AI Attendance System",
        description="Platform-native attendance using shared Supabase student, teacher, subject, and biometric data.",
        relative_path="platform",
        stack="FastAPI integrated",
        entry_hint="Open /attendance inside the platform",
        allowed_roles=("student", "teacher", "admin"),
        platform_url="/attendance",
    ),
    "timetable": ModuleInfo(
        key="timetable",
        name="AI Timetable Generator",
        description="Platform-native timetable scheduler using shared Supabase teacher, subject, and section data.",
        relative_path="AItimetable",
        stack="FastAPI integrated",
        entry_hint="Open /timetable and generate inside the platform",
        allowed_roles=("admin",),
        platform_url="/timetable",
    ),
    "ats-resume": ModuleInfo(
        key="ats-resume",
        name="AI ATS Resume Scorer",
        description="Platform-native resume scoring and job-description matching.",
        relative_path="resume ats",
        stack="FastAPI integrated",
        entry_hint="Open /ats inside the platform",
        allowed_roles=("student",),
        platform_url="/ats",
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
        api_url_env_key="NOTES_TEST_API_URL",
        api_health_path="/health",
        command_env_key="NOTES_TEST_START_COMMAND",
        api_command_env_key="NOTES_TEST_API_START_COMMAND",
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
        command_env_key="ALUMNI_START_COMMAND",
        platform_url="/alumni/opportunities",
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
