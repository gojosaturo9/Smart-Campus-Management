from __future__ import annotations

from app.core.supabase_client import SupabaseError, eq, rest_insert, rest_select, rest_update


EVENT_COLUMNS = "id,title,description,event_type,starts_at,ends_at,location,created_by,created_at"


def list_events() -> list[dict]:
    try:
        return rest_select("events", {"select": EVENT_COLUMNS, "order": "starts_at.asc.nullslast,created_at.desc"})
    except SupabaseError:
        return []


def create_event(
    *,
    title: str,
    description: str,
    event_type: str,
    starts_at: str,
    ends_at: str,
    location: str,
    created_by: str,
) -> tuple[bool, str]:
    if not title.strip():
        return False, "Event title is required."
    try:
        rest_insert(
            "events",
            {
                "title": title.strip(),
                "description": description.strip() or None,
                "event_type": event_type.strip() or None,
                "starts_at": starts_at.strip() or None,
                "ends_at": ends_at.strip() or None,
                "location": location.strip() or None,
                "created_by": created_by,
            },
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Event created successfully."


def register_for_event(event_id: str, user_id: str) -> tuple[bool, str]:
    try:
        existing = rest_select(
            "event_registrations",
            {
                "select": "id,status",
                "event_id": eq(event_id),
                "user_id": eq(user_id),
                "limit": "1",
            },
        )
        if existing:
            if existing[0].get("status") == "registered":
                return False, "You are already registered for this event."
            rest_update(
                "event_registrations",
                {"id": eq(existing[0]["id"])},
                {"status": "registered"},
            )
            return True, "Registration restored."
        rest_insert(
            "event_registrations",
            {
                "event_id": event_id,
                "user_id": user_id,
                "status": "registered",
            },
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Registered for event."


def registration_counts() -> dict[str, int]:
    try:
        rows = rest_select("event_registrations", {"select": "event_id,status"})
    except SupabaseError:
        return {}
    counts: dict[str, int] = {}
    for row in rows:
        if row.get("status") == "registered":
            event_id = str(row.get("event_id"))
            counts[event_id] = counts.get(event_id, 0) + 1
    return counts


def registered_event_ids(user_id: str) -> set[str]:
    try:
        rows = rest_select(
            "event_registrations",
            {"select": "event_id,status", "user_id": eq(user_id), "status": eq("registered")},
        )
    except SupabaseError:
        return set()
    return {str(row["event_id"]) for row in rows}
