from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.roles import ROLE_LABELS, ROLE_NAV


templates = Jinja2Templates(directory=settings.templates_dir)
templates.env.globals["role_labels"] = ROLE_LABELS
templates.env.globals["role_nav"] = ROLE_NAV
