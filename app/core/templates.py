from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.alumni_mentorship import notifications_for_user
from app.core.roles import ROLE_LABELS, ROLE_NAV


def format_datetime(value: object) -> str:
    if not value:
        return ""
    text = str(value)
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y, %I:%M %p").lstrip("0")
    except ValueError:
        return text


templates = Jinja2Templates(directory=settings.templates_dir)
templates.env.globals["role_labels"] = ROLE_LABELS
templates.env.globals["role_nav"] = ROLE_NAV
templates.env.globals["navbar_notifications"] = notifications_for_user
templates.env.filters["format_datetime"] = format_datetime
