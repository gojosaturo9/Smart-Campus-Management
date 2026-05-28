from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html
import re
import smtplib
import ssl
import time

from app.core.config import settings
from app.core.supabase_client import SupabaseError, rest_insert


MAX_EMAIL_WORKERS = 6
_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_EMAIL_WORKERS)


def dispatch_attendance_emails(records: list[dict], *, subject_name: str, marked_date: str | None = None) -> dict:
    marked_date = marked_date or date.today().isoformat()
    queued = 0
    skipped = 0
    for record in records or []:
        email = str(record.get("email") or "").strip()
        if not _is_valid_email(email):
            skipped += 1
            continue
        payload = _build_attendance_email(record, subject_name, marked_date)
        _insert_email_log(record, email, payload, "queued")
        _EXECUTOR.submit(_send_attendance_email_job, record, email, payload)
        queued += 1
    return {"queued": queued, "skipped": skipped}


def _send_attendance_email_job(record: dict, email: str, payload: dict) -> None:
    last_error = ""
    for attempt in range(1, _smtp_retries() + 1):
        try:
            _send_message(email, payload["subject"], payload["body"], payload["html_body"])
            _insert_email_log(record, email, payload, "sent", attempt_count=attempt)
            return
        except Exception as exc:
            last_error = str(exc)
            if attempt < _smtp_retries():
                time.sleep(min(2 * attempt, 8))
    _insert_email_log(record, email, payload, "failed", error_message=last_error, attempt_count=_smtp_retries())


def _build_attendance_email(record: dict, subject_name: str, marked_date: str) -> dict:
    student_name = record.get("name") or "Student"
    status = "Present" if record.get("status") == "present" else "Absent"
    subject = f"Attendance Update: {subject_name} - {status}"
    body = (
        f"Hello {student_name},\n\n"
        f"Your attendance for {subject_name} has been marked on {marked_date}.\n\n"
        f"Status: {status}\n\n"
        "If this status looks incorrect, please contact your teacher with proof.\n\n"
        "Regards,\n"
        "Smart Campus Attendance System"
    )
    accent = "#15803d" if status == "Present" else "#b91c1c"
    html_body = f"""<!doctype html>
<html>
<body style="margin:0;background:#f6f8fb;font-family:Arial,sans-serif;color:#172033;">
  <div style="max-width:640px;margin:0 auto;padding:24px;">
    <div style="background:#0f172a;color:white;padding:20px;border-radius:12px 12px 0 0;">
      <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;">Smart Campus</div>
      <h2 style="margin:8px 0 0;font-size:24px;">Attendance Update</h2>
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-top:0;padding:22px;border-radius:0 0 12px 12px;">
      <p>Hello {html.escape(str(student_name))},</p>
      <p>Your attendance has been marked.</p>
      <div style="margin:18px 0;padding:16px;border:1px solid #e5e7eb;border-radius:10px;background:#fafafa;">
        <div style="font-size:13px;color:#64748b;">Subject</div>
        <div style="font-size:18px;font-weight:700;">{html.escape(subject_name)}</div>
        <div style="height:12px;"></div>
        <div style="font-size:13px;color:#64748b;">Status</div>
        <div style="font-size:20px;font-weight:800;color:{accent};">{status}</div>
        <div style="height:12px;"></div>
        <div style="font-size:13px;color:#64748b;">Date</div>
        <div style="font-size:16px;font-weight:700;">{html.escape(marked_date)}</div>
      </div>
      <p style="font-size:13px;color:#64748b;">If this status looks incorrect, please contact your teacher with proof.</p>
    </div>
  </div>
</body>
</html>"""
    return {"subject": subject, "body": body, "html_body": html_body}


def _send_message(to_email: str, subject: str, body: str, html_body: str) -> None:
    sender_email, sender_password = _email_credentials()
    message = MIMEMultipart()
    message["From"] = _smtp_from(sender_email)
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    if _smtp_mode() == "ssl":
        with smtplib.SMTP_SSL(_smtp_host(), _smtp_ssl_port(), timeout=30) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        return

    with smtplib.SMTP(_smtp_host(), _smtp_tls_port(), timeout=30) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(sender_email, sender_password)
        server.send_message(message)


def _insert_email_log(record: dict, email: str, payload: dict, status: str, error_message: str = "", attempt_count: int = 0) -> None:
    try:
        rest_insert(
            "email_logs",
            {
                "student_id": record.get("student_id"),
                "to_email": email,
                "email_type": "attendance_update",
                "status": status,
                "subject": payload.get("subject"),
                "body_preview": str(payload.get("body") or "")[:500],
                "error_message": error_message or None,
                "attempt_count": attempt_count,
                "metadata": {
                    "student_name": record.get("name"),
                    "attendance_status": record.get("status"),
                    "roll_number": record.get("roll_number"),
                },
            },
        )
    except SupabaseError:
        return


def _email_credentials() -> tuple[str, str]:
    sender_email = _config("SMTP_USER") or _config("SENDER_EMAIL")
    sender_password = _config("SMTP_PASS") or _config("SENDER_PASSWORD")
    if not sender_email or not sender_password:
        raise RuntimeError("Email not configured. Add SMTP_USER/SMTP_PASS or SENDER_EMAIL/SENDER_PASSWORD.")
    return sender_email, sender_password.replace(" ", "")


def _config(name: str, default: str = "") -> str:
    return settings.env(name, default) or str(settings._secrets.get("email", {}).get(name.lower(), "")).strip()


def _smtp_host() -> str:
    return _config("SMTP_HOST", "smtp.gmail.com")


def _smtp_tls_port() -> int:
    return _config_int("SMTP_TLS_PORT", 587)


def _smtp_ssl_port() -> int:
    return _config_int("SMTP_SSL_PORT", 465)


def _smtp_mode() -> str:
    return _config("SMTP_SEND_MODE", "tls").lower()


def _smtp_from(sender_email: str) -> str:
    return _config("SMTP_FROM", sender_email) or sender_email


def _smtp_retries() -> int:
    return _config_int("SMTP_MAX_RETRIES", 3)


def _config_int(name: str, default: int) -> int:
    try:
        return int(_config(name, str(default)))
    except (TypeError, ValueError):
        return default


def _is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email or "")))
