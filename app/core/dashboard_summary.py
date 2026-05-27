from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.alumni import count_posts_by_type, list_alumni_posts
from app.core.analytics import admin_analytics_cards
from app.core.events import list_events, registration_counts
from app.core.module_catalog import MODULES
from app.core.roles import ADMIN, STUDENT, TEACHER
from app.core.supabase_client import SupabaseError, rest_select
from app.core.timetable_view import latest_timetable_for_user


@dataclass(frozen=True)
class DashboardSummary:
    today_name: str
    today_timetable: list[dict]
    next_class: dict | None
    upcoming_events: list[dict]
    alumni_counts: dict[str, int]
    admin_stats: dict[str, str]


def dashboard_summary_for_user(user: dict) -> DashboardSummary:
    today_name = datetime.now().strftime("%A")
    timetable = latest_timetable_for_user(user)
    today_entries = [entry for entry in timetable.entries if entry["day"] == today_name]
    return DashboardSummary(
        today_name=today_name,
        today_timetable=today_entries,
        next_class=today_entries[0] if today_entries else None,
        upcoming_events=list_events()[:5],
        alumni_counts=count_posts_by_type() if user["role"] in {STUDENT, ADMIN} else {},
        admin_stats=_admin_stats() if user["role"] == ADMIN else {},
    )


def _admin_stats() -> dict[str, str]:
    module_total = len(MODULES)
    online_modules = sum(1 for module in MODULES.values() if module.health == "online")
    event_counts = registration_counts()
    alumni_total = sum(count_posts_by_type().values())
    return {
        "module_health": f"{online_modules}/{module_total}",
        "timetable_runs": str(_timetable_run_count()),
        "event_registrations": str(sum(event_counts.values())),
        "alumni_posts": str(alumni_total),
        "analytics_cards": str(len(admin_analytics_cards())),
    }


def _timetable_run_count() -> int:
    try:
        rows = rest_select("SchedulerApp_timetablerun", {"select": "id"})
    except SupabaseError:
        return 0
    return len(rows)
