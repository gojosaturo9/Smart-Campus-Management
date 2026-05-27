from __future__ import annotations

import socket
import subprocess
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings
from app.core.module_catalog import ModuleInfo


@dataclass(frozen=True)
class ModuleProcessStatus:
    state: str
    detail: str
    log_path: Path


_PROCESSES: dict[str, subprocess.Popen] = {}


def registry_path() -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / "module_processes.json"


def log_path_for(module: ModuleInfo) -> Path:
    log_dir = settings.data_dir / "module_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{module.key}.log"


def get_process_status(module: ModuleInfo) -> ModuleProcessStatus:
    process = _PROCESSES.get(module.key)
    log_path = log_path_for(module)
    if process and process.poll() is None:
        return ModuleProcessStatus("running", f"PID {process.pid}", log_path)
    if process:
        _remove_registry_entry(module.key)
        return ModuleProcessStatus("stopped", f"Exited with code {process.returncode}", log_path)
    registry_entry = _registry().get(module.key)
    if registry_entry:
        pid = int(registry_entry.get("pid", 0))
        if pid and _pid_is_running(pid):
            return ModuleProcessStatus(
                "running",
                f"PID {pid} started at {registry_entry.get('started_at', 'unknown time')}",
                log_path,
            )
        _remove_registry_entry(module.key)
    if module.launch_url and _port_accepts_connections(module.launch_url):
        return ModuleProcessStatus("online", "Port is already accepting connections", log_path)
    return ModuleProcessStatus("stopped", "No process started by Smart Campus", log_path)


def start_module(module: ModuleInfo) -> tuple[bool, str]:
    if not module.exists:
        return False, "Module folder was not found."
    if not module.start_command:
        return False, "Start command is not configured."

    process = _PROCESSES.get(module.key)
    if process and process.poll() is None:
        return False, f"Module is already running as PID {process.pid}."

    if module.launch_url and _port_accepts_connections(module.launch_url):
        return False, "Launch URL port is already in use. Open the module or stop the existing server first."

    log_path = log_path_for(module)
    with log_path.open("ab") as log_file:
        log_file.write(_log_header(module).encode("utf-8"))
        process = subprocess.Popen(
            module.start_command,
            cwd=module.path,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            shell=True,
        )
    _PROCESSES[module.key] = process
    _set_registry_entry(module.key, process.pid, module.start_command, log_path)
    return True, f"Started {module.name} as PID {process.pid}."


def start_module_command(module: ModuleInfo, command: str, process_key: str, url: str = "") -> tuple[bool, str]:
    if not module.exists:
        return False, "Module folder was not found."
    if not command:
        return False, "Start command is not configured."

    process = _PROCESSES.get(process_key)
    if process and process.poll() is None:
        return False, f"Process is already running as PID {process.pid}."

    if url and _port_accepts_connections(url):
        return False, "Target port is already accepting connections."

    log_path = log_path_for(module)
    with log_path.open("ab") as log_file:
        log_file.write(_log_header(module, command, process_key).encode("utf-8"))
        process = subprocess.Popen(
            command,
            cwd=module.path,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            shell=True,
        )
    _PROCESSES[process_key] = process
    _set_registry_entry(process_key, process.pid, command, log_path)
    return True, f"Started {process_key} as PID {process.pid}."


def stop_module(module: ModuleInfo) -> tuple[bool, str]:
    process = _PROCESSES.get(module.key)
    if not process or process.poll() is not None:
        return False, "No Smart Campus-started process is running for this module."
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)
    _remove_registry_entry(module.key)
    return True, f"Stopped {module.name}."


def read_log_tail(module: ModuleInfo, max_chars: int = 12000) -> str:
    log_path = log_path_for(module)
    if not log_path.exists():
        return "No logs written yet."
    content = log_path.read_text(encoding="utf-8", errors="replace")
    return content[-max_chars:] if len(content) > max_chars else content


def _port_accepts_connections(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.hostname:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((parsed.hostname, port), timeout=0.75):
            return True
    except OSError:
        return False


def _registry() -> dict:
    path = registry_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_registry(registry: dict) -> None:
    registry_path().write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _set_registry_entry(module_key: str, pid: int, command: str, log_path: Path) -> None:
    registry = _registry()
    registry[module_key] = {
        "pid": pid,
        "command": command,
        "log_path": str(log_path),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_registry(registry)


def _remove_registry_entry(module_key: str) -> None:
    registry = _registry()
    if module_key in registry:
        del registry[module_key]
        _write_registry(registry)


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _log_header(module: ModuleInfo, command: str | None = None, process_key: str | None = None) -> str:
    return (
        "\n\n--- Smart Campus module start ---\n"
        f"module={process_key or module.key}\n"
        f"started_at={datetime.now(timezone.utc).isoformat()}\n"
        f"command={command or module.start_command}\n"
        "--- output ---\n"
    )
