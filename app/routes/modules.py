from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.session import get_current_user
from app.core.module_catalog import MODULES, PLACEHOLDER_MODULES
from app.core.templates import templates

router = APIRouter(prefix="/modules")


@router.get("/{module_key}")
def module_page(
    module_key: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    role = user["role"]

    if module_key in MODULES:
        module = MODULES[module_key]
        if role not in module.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/forbidden"},
            )
        return templates.TemplateResponse(
            "modules/module_detail.html",
            {"request": request, "user": user, "module": module},
        )

    if module_key in PLACEHOLDER_MODULES:
        name, allowed_roles = PLACEHOLDER_MODULES[module_key]
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/forbidden"},
            )
        return templates.TemplateResponse(
            "modules/placeholder.html",
            {"request": request, "user": user, "name": name},
        )

    raise HTTPException(status_code=404, detail="Module not found")
