# Smart Campus Platform - Resume Guide

Read this file first whenever work resumes on this project.

## Current Goal

Build one unified Python-based EdTech web platform named **Smart Campus Management Platform**.

The platform must combine multiple existing AI submodules behind one role-based dashboard:

- AI Attendance System
- AI Timetable Generator
- AI ATS Resume Scorer
- AI Notes-to-Test Generator
- Alumni connection features

The user does **not** want React as the unified shell. The unified shell should stay Python-based.

Recommended stack for the shell:

- FastAPI
- Jinja2 templates
- HTML/CSS
- Session-based auth first, database-backed auth later

## Existing Workspace

The project root is:

```text
C:\Users\anike\OneDrive\Desktop\SmartCampus
```

Current modules:

```text
SmartCampus/
  platform/          New unified Python shell created in Phase 1
  TruePresence/      AI attendance / face recognition module
  AItimetable/       AI timetable generator module
  resume ats/        AI ATS resume scorer module
  Testmodule/        AI notes-to-test generator module
  alumini/           Alumni module folder
```

Important rule:

```text
Do not modify existing submodule code unless the user explicitly asks.
Use existing modules as read-only integration targets first.
```

## Phase 1 Status - Completed

Created:

```text
platform/
  app/
    main.py
    auth/
      routes.py
      session.py
    core/
      config.py
      module_catalog.py
      roles.py
      templates.py
    routes/
      dashboard.py
      modules.py
    templates/
      base_dashboard.html
      base_public.html
      auth/login.html
      dashboard/dashboard.html
      modules/module_detail.html
      modules/placeholder.html
      errors/forbidden.html
    static/css/styles.css
  requirements.txt
  README.md
```

Implemented:

- FastAPI app entry point
- Jinja2 server-rendered UI
- Login page
- Role selection for demo login
- Session-based RBAC
- Protected role routes
- Common dashboard shell
- Sidebar navigation
- Header and logout
- Placeholder dashboards for:
  - Student
  - Teacher
  - Admin
  - Alumni
- Read-only module catalog that detects existing module folders

Current local URL:

```text
http://127.0.0.1:9000
```

Run command:

```powershell
cd C:\Users\anike\OneDrive\Desktop\SmartCampus\platform
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

Verified:

```text
/login -> 200 OK
student login -> 303 /student/dashboard -> 200 OK
```

## Phase 2 Status - Completed

Implemented:

- SQLite-backed user database
- Seeded demo accounts
- Password hashing with PBKDF2
- Email/password login
- Session now stores real database user identity
- Server-side RBAC still enforced on protected routes
- Admin user management page
- Admin can create users
- Admin can enable/disable users
- Admin dashboard shows active user counts by role
- Module URLs moved to `.env`
- Module cards show basic health status
- Module detail pages show configured launch URL and open button

New files:

```text
platform/.env
platform/.env.example
platform/data/smartcampus.db
platform/app/core/db.py
platform/app/core/security.py
platform/app/core/users.py
platform/app/routes/admin.py
platform/app/templates/admin/users.html
```

Demo accounts:

```text
admin@campus.local / Admin@123
student@campus.local / Student@123
teacher@campus.local / Teacher@123
alumni@campus.local / Alumni@123
```

Admin user management URL:

```text
http://127.0.0.1:9000/admin/users
```

Phase 2 verification:

```text
/login -> 200 OK
admin login -> 303 /admin/dashboard -> 200 OK
/admin/users as admin -> 200 OK
/admin/users as student -> 303 /forbidden?needed=admin
```

## Role Requirements

Student should access:

- Attendance
- Alumni connection
- ATS resume scorer
- Events
- AI Notes-to-Test
- Google Classroom features
- Helpdesk/Profile

Teacher should access:

- Google Classroom/send notes/info
- Attendance portal
- Notes-to-Test generator
- Own AI timetable view

Admin should access:

- Create teacher accounts
- Student/teacher analytics
- Generate AI timetable
- Manage events/seminars
- Manage alumni meetups

Alumni should access:

- Connect with students
- Chat/guidance
- Post internships/jobs

## Existing Module Notes

### TruePresence

Path:

```text
../TruePresence/AI-powered-attendance-platform
```

Stack:

```text
Streamlit + Python AI
```

Known run style:

```powershell
streamlit run app.py
```

Previously ran on:

```text
http://127.0.0.1:8503
```

### AItimetable

Path:

```text
../AItimetable
```

Stack:

```text
Django
```

Known run style:

```powershell
python manage.py runserver
```

Default URL:

```text
http://127.0.0.1:8000
```

### Resume ATS

Path:

```text
../resume ats
```

Stack:

```text
FastAPI backend + Streamlit frontend
```

Known run style from README:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
streamlit run frontend/streamlit_app.py
```

### Testmodule

Path:

```text
../Testmodule
```

Stack:

```text
FastAPI backend + frontend
```

Purpose:

```text
PDF/DOCX notes upload and AI quiz/test generation.
```

### Alumini

Path:

```text
../alumini
```

Status:

```text
Folder exists, integration still pending.
```

## Recommended Phase 3

Phase 3 should improve the dashboard product experience and connect modules more deeply.

## Supabase Migration Plan

The user wants SQLite removed and Supabase used for all platform/module data.

Created migration files:

```text
platform/supabase/schema.sql
platform/secrets.toml.example
```

To create tables:

1. Open Supabase project dashboard.
2. Go to SQL Editor.
3. Copy all SQL from `platform/supabase/schema.sql`.
4. Run it.
5. Create the first admin user in Supabase Auth.
6. Insert that admin user's profile row in `public.profiles`.
7. Copy `platform/secrets.toml.example` to `platform/secrets.toml`.
8. Fill Supabase URL, anon key, and service role key.

After that, replace the current SQLite auth code with Supabase Auth + `profiles`.

Required Supabase values:

```text
Project URL
Anon public key
Service role key
First admin user email/password
```

Important:

```text
Never commit real secrets.toml.
Only commit secrets.toml.example.
```

### 1. Improve Role Dashboards

Student dashboard cards:

- Attendance status placeholder
- Resume score shortcut
- Notes-to-Test shortcut
- Upcoming events
- Alumni opportunities

Teacher dashboard cards:

- Attendance portal shortcut
- Notes upload/classroom shortcut
- Notes-to-Test shortcut
- Timetable shortcut

Admin dashboard cards:

- Total users
- Total teachers
- Total students
- Module health
- Events management

Alumni dashboard cards:

- Post job/internship
- Guidance requests
- Student messages placeholder

### 2. Add Module Launch Controls

Current Phase 2 can open configured module URLs, but it does not start/stop submodule servers.

Next tasks:

- Add "Start module" actions for local development
- Add per-module process tracking
- Add safer port checks
- Add module logs page
- Keep commands configurable, not hardcoded into templates

### 3. Connect Data Across Modules

Tasks:

- Create shared student/teacher identity model
- Map platform users to submodule users
- Add single sign-on style redirects if possible
- Add API proxy routes for modules that expose FastAPI endpoints
- Start with ATS and Notes-to-Test because they already have FastAPI backends
- Keep Streamlit/Django modules launched separately until stable

## Recommended Phase 4

Phase 4 should add admin analytics.

Tasks:

- Attendance analytics cards
- ATS usage stats
- Quiz/test generation stats
- Timetable generation history
- Event participation stats
- Alumni opportunity counts

## Recommended Phase 5

Phase 5 should improve production readiness.

Tasks:

- Move secrets to `.env`
- Add production session secret
- Add database migrations
- Add audit logs
- Add error pages
- Add test coverage for RBAC
- Add Docker setup for platform
- Add service startup scripts for all modules

## Development Rules

- Keep all new unified-platform work inside `platform/` unless instructed otherwise.
- Do not rewrite existing submodules during early integration.
- Prefer small, working phases.
- Verify routes after each major change.
- Keep RBAC checks server-side, not only in templates.
- Avoid hardcoding real secrets.
- Use `.env` for URLs and secrets when Phase 2 starts.

## Next Best Command When Resuming

First inspect current state:

```powershell
cd C:\Users\anike\OneDrive\Desktop\SmartCampus
Get-ChildItem -Force
Get-ChildItem -Force .\platform
```

Then run the platform:

```powershell
cd C:\Users\anike\OneDrive\Desktop\SmartCampus\platform
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

Open:

```text
http://127.0.0.1:9000
```
