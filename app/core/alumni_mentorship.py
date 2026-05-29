from __future__ import annotations

from datetime import datetime, timezone

from app.core.roles import ALUMNI, STUDENT
from app.core.supabase_client import SupabaseError, eq, is_configured, rest_delete, rest_insert, rest_select, rest_update
from app.core.users import public_user


REQUEST_COLUMNS = "id,student_id,alumni_id,intent,message,status,created_at,updated_at"
CONNECTION_COLUMNS = "id,student_id,alumni_id,request_id,status,created_at,updated_at"
MESSAGE_COLUMNS = "id,connection_id,sender_id,message,created_at,read_at"
MESSAGE_COLUMNS_WITH_ATTACHMENT = (
    "id,connection_id,sender_id,message,created_at,read_at,"
    "attachment_filename,attachment_content_type,attachment_size,attachment_path"
)
NOTIFICATION_COLUMNS = "id,user_id,title,body,is_read,related_connection_id,created_at"
PROFILE_COLUMNS = "id,full_name,email,role,avatar_url,is_active,created_at"
STUDENT_PROFILE_COLUMNS = "profile_id,roll_number,sections(name,semester,academic_year,departments(name,code),branches(name,code))"


def mentorship_workspace(user: dict) -> dict:
    if not is_configured():
        return _empty_workspace(user, "Supabase is not configured.")
    try:
        if user["role"] == STUDENT:
            return _student_workspace(user)
        if user["role"] == ALUMNI:
            return _alumni_workspace(user)
    except SupabaseError as exc:
        return _empty_workspace(
            user,
            f"{exc}. Run the alumni mentorship Supabase migration if these tables are not created yet.",
        )
    return _empty_workspace(user, "Only student and alumni roles can use mentorship.")


def create_mentorship_request(*, student_id: str, alumni_id: str, intent: str, message: str) -> tuple[bool, str]:
    clean_intent = intent.strip()
    clean_message = message.strip()
    if not alumni_id:
        return False, "Select an alumni mentor."
    if not clean_intent:
        return False, "Request intent is required."
    if not clean_message:
        return False, "Request message is required."
    try:
        existing_connection = rest_select(
            "alumni_mentorship_connections",
            {
                "select": "id,status",
                "student_id": eq(student_id),
                "alumni_id": eq(alumni_id),
                "status": eq("active"),
                "limit": "1",
            },
        )
        if existing_connection:
            return False, "You are already connected with this mentor."
        existing_request = rest_select(
            "alumni_mentorship_requests",
            {
                "select": "id,status",
                "student_id": eq(student_id),
                "alumni_id": eq(alumni_id),
                "status": eq("pending"),
                "limit": "1",
            },
        )
        if existing_request:
            return False, "A pending request already exists for this mentor."
        rest_insert(
            "alumni_mentorship_requests",
            {
                "student_id": student_id,
                "alumni_id": alumni_id,
                "intent": clean_intent,
                "message": clean_message,
                "status": "pending",
            },
        )
        _notify(
            user_id=alumni_id,
            title="New mentorship request",
            body=f"A student requested help with {clean_intent}.",
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Mentorship request sent."


def accept_mentorship_request(*, request_id: str, alumni_id: str) -> tuple[bool, str]:
    try:
        rows = rest_select(
            "alumni_mentorship_requests",
            {
                "select": REQUEST_COLUMNS,
                "id": eq(request_id),
                "alumni_id": eq(alumni_id),
                "limit": "1",
            },
        )
        if not rows:
            return False, "Request not found."
        request = rows[0]
        if request.get("status") == "accepted":
            return False, "Request is already accepted."
        connection = rest_insert(
            "alumni_mentorship_connections",
            {
                "student_id": request["student_id"],
                "alumni_id": alumni_id,
                "request_id": request_id,
                "status": "active",
            },
        )[0]
        rest_update(
            "alumni_mentorship_requests",
            {"id": eq(request_id)},
            {"status": "accepted"},
        )
        _notify(
            user_id=request["student_id"],
            title="Mentorship request accepted",
            body="Your alumni mentor accepted the request. You can start the conversation now.",
            connection_id=connection["id"],
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Request accepted and connection created."


def reject_mentorship_request(*, request_id: str, alumni_id: str) -> tuple[bool, str]:
    try:
        rows = rest_update(
            "alumni_mentorship_requests",
            {"id": eq(request_id), "alumni_id": eq(alumni_id)},
            {"status": "rejected"},
        )
        if not rows:
            return False, "Request not found."
        _notify(
            user_id=rows[0]["student_id"],
            title="Mentorship request update",
            body="Your mentorship request was not accepted at this time.",
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Request rejected."


def send_message(*, connection_id: str, sender_id: str, message: str, attachment: dict | None = None) -> tuple[bool, str]:
    clean_message = message.strip()
    if not connection_id:
        return False, "Open a mentorship connection before sending a message."
    if not clean_message and not attachment:
        return False, "Message or attachment is required."
    try:
        connection = _connection_for_user(connection_id, sender_id)
        if not connection:
            return False, "Connection not found."
        payload = _message_payload(connection_id=connection_id, sender_id=sender_id, message=clean_message, attachment=attachment)
        rest_insert("alumni_mentorship_messages", payload)
        receiver_id = connection["alumni_id"] if sender_id == connection["student_id"] else connection["student_id"]
        _notify(
            user_id=receiver_id,
            title="New mentorship message",
            body=(clean_message or f"Sent attachment: {attachment.get('filename', 'file') if attachment else 'file'}")[:120],
            connection_id=connection_id,
        )
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Message sent."


def create_message(*, connection_id: str, sender_id: str, message: str, attachment: dict | None = None) -> tuple[bool, str, dict | None]:
    clean_message = message.strip()
    if not connection_id:
        return False, "Open a mentorship connection before sending a message.", None
    if not clean_message and not attachment:
        return False, "Message or attachment is required.", None
    try:
        connection = _connection_for_user(connection_id, sender_id)
        if not connection:
            return False, "Connection not found.", None
        payload = _message_payload(connection_id=connection_id, sender_id=sender_id, message=clean_message, attachment=attachment)
        rows = rest_insert("alumni_mentorship_messages", payload)
        receiver_id = connection["alumni_id"] if sender_id == connection["student_id"] else connection["student_id"]
        _notify(
            user_id=receiver_id,
            title="New mentorship message",
            body=(clean_message or f"Sent attachment: {attachment.get('filename', 'file') if attachment else 'file'}")[:120],
            connection_id=connection_id,
        )
    except SupabaseError as exc:
        return False, str(exc), None
    return True, "Message sent.", rows[0] if rows else None


def _message_payload(*, connection_id: str, sender_id: str, message: str, attachment: dict | None) -> dict:
    payload = {
        "connection_id": connection_id,
        "sender_id": sender_id,
        "message": message,
    }
    if attachment:
        payload.update(
            {
                "attachment_filename": attachment.get("filename", ""),
                "attachment_content_type": attachment.get("content_type", ""),
                "attachment_size": int(attachment.get("size") or 0),
                "attachment_path": attachment.get("path", ""),
            }
        )
    return payload


def messages_for_connection(*, connection_id: str, user_id: str, after_id: str = "") -> tuple[bool, str, list[dict]]:
    try:
        connection = _connection_for_user(connection_id, user_id)
        if not connection:
            return False, "Connection not found.", []
        rows = _select_messages(
            {
                "connection_id": eq(connection_id),
                "order": "created_at.asc",
                "limit": "100",
            }
        )
    except SupabaseError as exc:
        return False, str(exc), []
    if after_id:
        seen = False
        filtered = []
        for row in rows:
            if seen:
                filtered.append(row)
            elif row.get("id") == after_id:
                seen = True
        rows = filtered if seen else rows
    return True, "Messages loaded.", rows


def mark_connection_read(*, connection_id: str, user_id: str) -> tuple[bool, str]:
    try:
        connection = _connection_for_user(connection_id, user_id)
        if not connection:
            return False, "Connection not found."
        rows = rest_select(
            "alumni_mentorship_messages",
            {
                "select": "id,sender_id,read_at",
                "connection_id": eq(connection_id),
                "limit": "100",
            },
        )
        for row in rows:
            if row.get("sender_id") != user_id and not row.get("read_at"):
                rest_update("alumni_mentorship_messages", {"id": eq(row["id"])}, {"read_at": datetime.now(timezone.utc).isoformat()})
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Messages marked read."


def message_attachment_for_user(*, message_id: str, user_id: str) -> tuple[bool, str, dict | None]:
    try:
        rows = _select_messages({"id": eq(message_id), "limit": "1"})
        if not rows:
            return False, "Attachment not found.", None
        message = rows[0]
        if not message.get("attachment_path"):
            return False, "Attachment not found.", None
        connection = _connection_for_user(message["connection_id"], user_id)
        if not connection:
            return False, "Attachment not found.", None
    except SupabaseError as exc:
        return False, str(exc), None
    return True, "Attachment ready.", message


def delete_message_for_user(*, message_id: str, user_id: str) -> tuple[bool, str]:
    try:
        rows = _select_messages({"id": eq(message_id), "limit": "1"})
        if not rows:
            return False, "Message not found."
        message = rows[0]
        connection = _connection_for_user(message["connection_id"], user_id)
        if not connection:
            return False, "Message not found."
        rest_delete("alumni_mentorship_messages", {"id": eq(message_id)})
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Message deleted."


def edit_message_for_user(*, message_id: str, user_id: str, message: str) -> tuple[bool, str, dict | None]:
    clean_message = message.strip()
    if not clean_message:
        return False, "Message cannot be empty.", None
    try:
        rows = _select_messages({"id": eq(message_id), "limit": "1"})
        if not rows:
            return False, "Message not found.", None
        existing = rows[0]
        if existing.get("sender_id") != user_id:
            return False, "Only the sender can edit this message.", None
        connection = _connection_for_user(existing["connection_id"], user_id)
        if not connection:
            return False, "Message not found.", None
        updated = rest_update("alumni_mentorship_messages", {"id": eq(message_id)}, {"message": clean_message})
    except SupabaseError as exc:
        return False, str(exc), None
    return True, "Message updated.", updated[0] if updated else {**existing, "message": clean_message}


def delete_connection_messages_for_user(*, connection_id: str, user_id: str) -> tuple[bool, str]:
    try:
        connection = _connection_for_user(connection_id, user_id)
        if not connection:
            return False, "Chat not found."
        rest_delete("alumni_mentorship_messages", {"connection_id": eq(connection_id)})
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Chat messages deleted."


def delete_notification(*, notification_id: str, user_id: str) -> tuple[bool, str]:
    try:
        rows = rest_select(
            "alumni_mentorship_notifications",
            {
                "select": "id",
                "id": eq(notification_id),
                "user_id": eq(user_id),
                "limit": "1",
            },
        )
        if not rows:
            return False, "Notification not found."
        rest_delete("alumni_mentorship_notifications", {"id": eq(notification_id), "user_id": eq(user_id)})
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Notification deleted."


def notifications_for_user(user_id: str) -> list[dict]:
    try:
        return _notifications_for_user(user_id)
    except Exception:
        return []


def mentorship_counts_for_user(workspace: dict) -> dict[str, int]:
    return {
        "mentors": len(workspace.get("mentors", [])),
        "mentees": len(workspace.get("connections", [])),
        "requests": len(workspace.get("requests", [])),
        "active_threads": len(workspace.get("connections", [])),
    }


def admin_mentorship_overview() -> dict:
    try:
        requests = rest_select("alumni_mentorship_requests", {"select": REQUEST_COLUMNS, "order": "created_at.desc"})
        connections = rest_select("alumni_mentorship_connections", {"select": CONNECTION_COLUMNS, "order": "created_at.desc"})
        messages = rest_select("alumni_mentorship_messages", {"select": MESSAGE_COLUMNS, "order": "created_at.desc", "limit": "10"})
        total_messages = len(rest_select("alumni_mentorship_messages", {"select": "id"}))
        pending_alumni = rest_select(
            "profiles",
            {"select": PROFILE_COLUMNS, "role": eq(ALUMNI), "is_active": eq("false"), "order": "created_at.desc"},
        )
    except SupabaseError as exc:
        return {
            "error": str(exc),
            "metrics": [],
            "pending_alumni": [],
            "pending_requests": [],
            "active_connections": [],
            "recent_messages": [],
        }

    user_ids = set()
    for row in requests + connections:
        user_ids.add(row.get("student_id", ""))
        user_ids.add(row.get("alumni_id", ""))
    for row in messages:
        user_ids.add(row.get("sender_id", ""))
    profiles = _profiles_map(user_ids)

    pending_requests = []
    for row in requests:
        if row.get("status") == "pending":
            pending_requests.append({**row, "student": profiles.get(row["student_id"], {}), "alumni": profiles.get(row["alumni_id"], {})})

    active_connections = []
    for row in connections:
        if row.get("status") == "active":
            active_connections.append({**row, "student": profiles.get(row["student_id"], {}), "alumni": profiles.get(row["alumni_id"], {})})

    recent_messages = []
    for row in messages:
        recent_messages.append({**row, "sender": profiles.get(row["sender_id"], {})})

    return {
        "error": "",
        "metrics": [
            {"label": "Pending alumni", "value": len(pending_alumni), "detail": "Awaiting admin approval"},
            {"label": "Pending requests", "value": len(pending_requests), "detail": "Student requests waiting for alumni"},
            {"label": "Active connections", "value": len(active_connections), "detail": "Open mentorship relationships"},
            {"label": "Messages", "value": total_messages, "detail": "Total mentorship messages"},
        ],
        "pending_alumni": [public_user(row) for row in pending_alumni],
        "pending_requests": pending_requests[:10],
        "active_connections": active_connections[:10],
        "recent_messages": recent_messages,
    }


def _student_workspace(user: dict) -> dict:
    mentors = _profiles_by_role(ALUMNI)
    requests = _requests_for_student(user["id"])
    connections = _connections_for_user(user["id"])
    messages = _messages_for_connections(connections)
    active_connection_id = connections[0]["id"] if connections else ""
    return _base_workspace(
        user,
        mentors=mentors,
        requests=requests,
        connections=_attach_connection_activity(_hydrate_connections(connections, user["id"]), messages, user["id"]),
        active_connection_id=active_connection_id,
        messages=messages,
        notifications=_notifications_for_user(user["id"]),
    )


def _alumni_workspace(user: dict) -> dict:
    requests = _requests_for_alumni(user["id"])
    connections = _connections_for_user(user["id"])
    messages = _messages_for_connections(connections)
    active_connection_id = connections[0]["id"] if connections else ""
    return _base_workspace(
        user,
        mentors=[],
        requests=requests,
        connections=_attach_connection_activity(_hydrate_connections(connections, user["id"]), messages, user["id"]),
        active_connection_id=active_connection_id,
        messages=messages,
        notifications=_notifications_for_user(user["id"]),
    )


def _base_workspace(
    user: dict,
    *,
    mentors: list[dict],
    requests: list[dict],
    connections: list[dict],
    active_connection_id: str,
    messages: dict[str, list[dict]],
    notifications: list[dict],
    setup_error: str = "",
) -> dict:
    return {
        "role": user.get("role", ""),
        "profile": _profile_for_role(user),
        "mentors": mentors,
        "requests": requests,
        "connections": connections,
        "active_connection_id": active_connection_id,
        "messages": messages,
        "notifications": notifications,
        "quick_replies": _quick_replies(user.get("role", "")),
        "setup_error": setup_error,
    }


def _empty_workspace(user: dict, setup_error: str) -> dict:
    return _base_workspace(
        user,
        mentors=[],
        requests=[],
        connections=[],
        active_connection_id="",
        messages={},
        notifications=[],
        setup_error=setup_error,
    )


def _profile_for_role(user: dict) -> dict:
    if user.get("role") == ALUMNI:
        return {
            "name": user.get("name") or "Alumni Mentor",
            "title": "Verified alumni mentor",
            "focus": "Career guidance, resumes, interviews",
        }
    return {
        "name": user.get("name") or "Student",
        "title": "Student mentee",
        "focus": "Mentorship, internships, placement preparation",
    }


def _profiles_by_role(role: str) -> list[dict]:
    rows = rest_select(
        "profiles",
        {"select": PROFILE_COLUMNS, "role": eq(role), "is_active": eq("true"), "order": "full_name.asc"},
    )
    users = [public_user(row) for row in rows]
    if role != ALUMNI:
        return users
    profile_rows = rest_select(
        "alumni_profiles",
        {"select": "profile_id,graduation_year,company,job_title,linkedin_url,bio"},
    )
    alumni_meta = {str(row.get("profile_id")): row for row in profile_rows}
    enriched = []
    for user in users:
        meta = alumni_meta.get(user["id"], {})
        enriched.append(
            {
                **user,
                "graduation_year": meta.get("graduation_year") or "",
                "company": meta.get("company") or "",
                "job_title": meta.get("job_title") or "",
                "linkedin_url": meta.get("linkedin_url") or "",
                "bio": meta.get("bio") or "",
            }
        )
    return enriched


def _profile_by_id(user_id: str) -> dict:
    rows = rest_select("profiles", {"select": PROFILE_COLUMNS, "id": eq(user_id), "limit": "1"})
    return public_user(rows[0]) if rows else {}


def _profiles_map(user_ids: set[str]) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    for user_id in user_ids:
        if user_id:
            profiles[user_id] = _profile_by_id(user_id)
    return profiles


def _requests_for_student(student_id: str) -> list[dict]:
    rows = rest_select(
        "alumni_mentorship_requests",
        {"select": REQUEST_COLUMNS, "student_id": eq(student_id), "order": "created_at.desc"},
    )
    profiles = _profiles_map({row["alumni_id"] for row in rows})
    for row in rows:
        row["alumni"] = profiles.get(row["alumni_id"], {})
        row["status_label"] = _status_label(row.get("status", ""))
    return rows


def _requests_for_alumni(alumni_id: str) -> list[dict]:
    rows = rest_select(
        "alumni_mentorship_requests",
        {"select": REQUEST_COLUMNS, "alumni_id": eq(alumni_id), "status": eq("pending"), "order": "created_at.desc"},
    )
    profiles = _profiles_map({row["student_id"] for row in rows})
    academic_details = _student_academic_details_map({row["student_id"] for row in rows})
    for row in rows:
        row["student"] = {**profiles.get(row["student_id"], {}), "academic": academic_details.get(row["student_id"], {})}
        row["status_label"] = _status_label(row.get("status", ""))
    return rows


def _status_label(status: str) -> str:
    labels = {
        "pending": "Pending",
        "accepted": "Accepted",
        "rejected": "Rejected",
        "cancelled": "Cancelled",
    }
    return labels.get(status, status.title())


def _connections_for_user(user_id: str) -> list[dict]:
    return rest_select(
        "alumni_mentorship_connections",
        {
            "select": CONNECTION_COLUMNS,
            "or": f"(student_id.eq.{user_id},alumni_id.eq.{user_id})",
            "status": eq("active"),
            "order": "created_at.desc",
        },
    )


def _connection_for_user(connection_id: str, user_id: str) -> dict | None:
    rows = rest_select(
        "alumni_mentorship_connections",
        {
            "select": CONNECTION_COLUMNS,
            "id": eq(connection_id),
            "or": f"(student_id.eq.{user_id},alumni_id.eq.{user_id})",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


def _hydrate_connections(connections: list[dict], current_user_id: str) -> list[dict]:
    profiles = _profiles_map({row["student_id"] for row in connections} | {row["alumni_id"] for row in connections})
    student_details = _student_academic_details_map({row["student_id"] for row in connections})
    hydrated = []
    for row in connections:
        peer_id = row["alumni_id"] if current_user_id == row["student_id"] else row["student_id"]
        student_profile = {**profiles.get(row["student_id"], {}), "academic": student_details.get(row["student_id"], {})}
        hydrated.append(
            {
                **row,
                "student": student_profile,
                "alumni": profiles.get(row["alumni_id"], {}),
                "peer": profiles.get(row["alumni_id"], {}) if peer_id == row["alumni_id"] else student_profile,
            }
        )
    return hydrated


def _student_academic_details_map(student_ids: set[str]) -> dict[str, dict]:
    details: dict[str, dict] = {}
    for student_id in student_ids:
        if not student_id:
            continue
        try:
            rows = rest_select(
                "student_profiles",
                {"select": STUDENT_PROFILE_COLUMNS, "profile_id": eq(student_id), "limit": "1"},
            )
        except SupabaseError:
            rows = []
        if not rows:
            details[student_id] = _empty_academic_details()
            continue
        section = rows[0].get("sections") or {}
        department = section.get("departments") or {}
        branch = section.get("branches") or {}
        details[student_id] = {
            "roll_number": rows[0].get("roll_number") or "",
            "course": department.get("code") or department.get("name") or "",
            "branch": branch.get("code") or branch.get("name") or "",
            "semester": section.get("semester") or "",
            "section": section.get("name") or "",
            "academic_year": section.get("academic_year") or "",
        }
    return details


def _empty_academic_details() -> dict:
    return {
        "roll_number": "",
        "course": "",
        "branch": "",
        "semester": "",
        "section": "",
        "academic_year": "",
    }


def _attach_connection_activity(connections: list[dict], messages: dict[str, list[dict]], current_user_id: str) -> list[dict]:
    enriched = []
    for connection in connections:
        rows = messages.get(connection["id"], [])
        last = rows[-1] if rows else {}
        unread = [
            row
            for row in rows
            if row.get("sender_id") != current_user_id and not row.get("read_at")
        ]
        enriched.append(
            {
                **connection,
                "last_message": last.get("message") or "No messages yet",
                "last_message_at": last.get("created_at") or connection.get("created_at") or "",
                "unread_count": len(unread),
            }
        )
    return enriched


def _messages_for_connections(connections: list[dict]) -> dict[str, list[dict]]:
    messages: dict[str, list[dict]] = {}
    for connection in connections:
        rows = _select_messages(
            {
                "connection_id": eq(connection["id"]),
                "order": "created_at.asc",
                "limit": "100",
            }
        )
        messages[connection["id"]] = rows
    return messages


def _select_messages(query: dict[str, str]) -> list[dict]:
    try:
        return rest_select("alumni_mentorship_messages", {"select": MESSAGE_COLUMNS_WITH_ATTACHMENT, **query})
    except SupabaseError as exc:
        if "attachment_" not in str(exc):
            raise
        rows = rest_select("alumni_mentorship_messages", {"select": MESSAGE_COLUMNS, **query})
        for row in rows:
            row["attachment_filename"] = ""
            row["attachment_content_type"] = ""
            row["attachment_size"] = 0
            row["attachment_path"] = ""
        return rows


def _notifications_for_user(user_id: str) -> list[dict]:
    return rest_select(
        "alumni_mentorship_notifications",
        {
            "select": NOTIFICATION_COLUMNS,
            "user_id": eq(user_id),
            "order": "created_at.desc",
            "limit": "8",
        },
    )


def _notify(*, user_id: str, title: str, body: str, connection_id: str | None = None) -> None:
    rest_insert(
        "alumni_mentorship_notifications",
        {
            "user_id": user_id,
            "title": title,
            "body": body,
            "related_connection_id": connection_id,
        },
    )


def _quick_replies(role: str) -> list[str]:
    if role == ALUMNI:
        return [
            "Send your latest resume and GitHub link.",
            "Let us schedule a mock interview.",
            "Share the areas where you need the most help.",
        ]
    return [
        "I have uploaded my latest resume.",
        "Can we schedule a mock interview this week?",
        "I shared my GitHub profile for review.",
    ]
