from __future__ import annotations

from dataclasses import dataclass

from app.core.roles import ALL_ROLES
from app.core.supabase_client import SupabaseError, rest_select
from app.core.users import user_counts_by_role


@dataclass(frozen=True)
class MetricCard:
    label: str
    value: str
    detail: str


def admin_analytics_cards() -> tuple[MetricCard, ...]:
    counts = user_counts_by_role()
    total_users = sum(counts.values())

    return (
        MetricCard("Total users", str(total_users), _role_detail(counts)),
        MetricCard("Students", str(counts.get("student", 0)), "Active student profiles"),
        MetricCard("Teachers", str(counts.get("teacher", 0)), "Active teacher profiles"),
        MetricCard("ATS analyses", str(_count("ats_analyses")), "Resume analysis records in Supabase"),
        MetricCard("Quiz attempts", str(_count("quiz_attempts")), "Notes-to-Test attempt records in Supabase"),
        MetricCard("Events", str(_count("events")), "Campus events and seminars"),
        MetricCard("Alumni posts", str(_count("alumni_posts")), "Jobs, internships, and guidance posts"),
    )


def _count(table: str) -> int:
    try:
        rows = rest_select(table, {"select": "id"})
    except SupabaseError:
        return 0
    return len(rows)


def _role_detail(counts: dict[str, int]) -> str:
    return ", ".join(f"{role}: {counts.get(role, 0)}" for role in ALL_ROLES)
