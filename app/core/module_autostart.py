from app.core.module_catalog import MODULES, ModuleInfo
from app.core.module_processes import start_module_command


AUTO_START_ROLES = {"student", "teacher", "admin", "alumni"}


def autostart_modules_for_role(role: str) -> list[str]:
    if role not in AUTO_START_ROLES:
        return []

    results: list[str] = []
    for module in MODULES.values():
        if role not in module.allowed_roles:
            continue
        if module.platform_url:
            continue
        results.extend(_start_module_parts(module))
    return results


def _start_module_parts(module: ModuleInfo) -> list[str]:
    results: list[str] = []
    if module.api_start_command:
        ok, message = start_module_command(
            module,
            module.api_start_command,
            f"{module.key}-api",
            module.api_url,
        )
        if ok:
            results.append(message)

    if module.start_command:
        ok, message = start_module_command(
            module,
            module.start_command,
            module.key,
            module.launch_url,
        )
        if ok:
            results.append(message)
    return results
