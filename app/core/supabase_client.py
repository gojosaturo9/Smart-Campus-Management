from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.core.config import settings


class SupabaseError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(
        settings.supabase_url
        and settings.supabase_anon_key
        and settings.supabase_service_role_key
    )


def sign_in_with_password(email: str, password: str) -> dict:
    return _request(
        "POST",
        "/auth/v1/token",
        key=settings.supabase_anon_key,
        bearer=settings.supabase_anon_key,
        query={"grant_type": "password"},
        body={"email": email, "password": password},
    )


def admin_create_auth_user(email: str, password: str, full_name: str, role: str) -> dict:
    return _request(
        "POST",
        "/auth/v1/admin/users",
        key=settings.supabase_service_role_key,
        bearer=settings.supabase_service_role_key,
        body={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name, "role": role},
        },
    )


def rest_select(table: str, query: dict[str, str]) -> list[dict]:
    return _request(
        "GET",
        f"/rest/v1/{table}",
        key=settings.supabase_service_role_key,
        bearer=settings.supabase_service_role_key,
        query=query,
    )


def rest_insert(table: str, row: dict) -> list[dict]:
    return _request(
        "POST",
        f"/rest/v1/{table}",
        key=settings.supabase_service_role_key,
        bearer=settings.supabase_service_role_key,
        body=row,
        extra_headers={"Prefer": "return=representation"},
    )


def rest_update(table: str, filters: dict[str, str], values: dict) -> list[dict]:
    return _request(
        "PATCH",
        f"/rest/v1/{table}",
        key=settings.supabase_service_role_key,
        bearer=settings.supabase_service_role_key,
        query=filters,
        body=values,
        extra_headers={"Prefer": "return=representation"},
    )


def rest_delete(table: str, filters: dict[str, str]) -> list[dict]:
    return _request(
        "DELETE",
        f"/rest/v1/{table}",
        key=settings.supabase_service_role_key,
        bearer=settings.supabase_service_role_key,
        query=filters,
        extra_headers={"Prefer": "return=representation"},
    )


def _request(
    method: str,
    path: str,
    *,
    key: str,
    bearer: str,
    query: dict[str, str] | None = None,
    body: dict | None = None,
    extra_headers: dict[str, str] | None = None,
):
    if not settings.supabase_url:
        raise SupabaseError("Supabase URL is not configured.")

    url = settings.supabase_url.rstrip("/") + path
    if query:
        url += "?" + urlencode(query)

    data = None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=12) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SupabaseError(_friendly_error(detail) or f"Supabase request failed with HTTP {exc.code}.") from exc
    except URLError as exc:
        raise SupabaseError(f"Could not reach Supabase: {exc.reason}") from exc

    if not response_body:
        return []
    return json.loads(response_body)


def eq(value: str) -> str:
    return "eq." + quote(str(value), safe="")


def in_(values: list[str] | tuple[str, ...] | set[str]) -> str:
    encoded = ",".join(quote(str(value), safe="") for value in values)
    return f"in.({encoded})"


def _friendly_error(detail: str) -> str:
    try:
        parsed = json.loads(detail)
    except json.JSONDecodeError:
        return detail
    return parsed.get("msg") or parsed.get("message") or parsed.get("error_description") or detail
