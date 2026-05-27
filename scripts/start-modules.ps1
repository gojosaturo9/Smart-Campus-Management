$ErrorActionPreference = "Stop"

$Workspace = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$modules = @(
  @{
    Name = "AItimetable"
    Path = Join-Path $Workspace "AItimetable"
    Command = ".\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
  },
  @{
    Name = "ATS frontend"
    Path = Join-Path $Workspace "resume ats"
    Command = ".\.venv\Scripts\streamlit.exe run frontend/streamlit_app.py --server.address 127.0.0.1 --server.port 8504"
  },
  @{
    Name = "Notes-to-Test frontend"
    Path = Join-Path $Workspace "Testmodule\frontend"
    Command = "npm run dev -- --host 127.0.0.1 --port 5173"
  }
)

foreach ($module in $modules) {
  if (-not (Test-Path $module.Path)) {
    Write-Warning "$($module.Name) path not found: $($module.Path)"
    continue
  }
  Start-Process powershell -WindowStyle Hidden -WorkingDirectory $module.Path -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $module.Command
  )
  Write-Host "Started $($module.Name)"
}
