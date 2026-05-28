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

## Phase 3 Status - Completed

Implemented:

- Role-specific dashboard action cards for Student, Teacher, Admin, and Alumni portals
- Cleaner module cards with health and workspace detection badges
- Separate frontend URL and API URL health checks for ATS and Notes-to-Test
- Admin-only local module launch controls
- Admin-only module stop controls for processes started by Smart Campus
- Per-module process status on module detail pages
- Per-module log files under `platform/data/module_logs`
- Module logs page at `/modules/{module_key}/logs`
- Configurable module start commands in `.env`, not templates
- Faster health checks so offline modules do not stall dashboards

New files:

```text
platform/app/core/dashboard_cards.py
platform/app/core/module_processes.py
platform/app/templates/modules/module_logs.html
```

New `.env` values:

```text
ATS_BACKEND_URL=http://127.0.0.1:8001
NOTES_TEST_API_URL=http://127.0.0.1:8002

ATTENDANCE_START_COMMAND=streamlit run app.py --server.address 127.0.0.1 --server.port 8503
TIMETABLE_START_COMMAND=python manage.py runserver 127.0.0.1:8000
ATS_START_COMMAND=streamlit run frontend/streamlit_app.py --server.address 127.0.0.1 --server.port 8504
NOTES_TEST_START_COMMAND=cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
ALUMNI_START_COMMAND=
```

Phase 3 verification:

```text
compileall app -> passed
/login -> 200 OK
admin login -> /admin/dashboard -> 200 OK
/modules/attendance as admin -> 200 OK
/modules/attendance/logs as admin -> 200 OK
student login -> /student/dashboard -> 200 OK
/modules/notes-to-test as student -> 200 OK
```

Current local URL:

```text
http://127.0.0.1:9000
```

## Supabase Auth Migration Status - Completed

Implemented:

- Platform login now uses Supabase Auth password sign-in
- Session user identity now uses Supabase Auth UUIDs instead of SQLite integer ids
- Role, display name, email, and active status load from `public.profiles`
- Admin user list now reads from `public.profiles`
- Admin user creation now creates a Supabase Auth user and matching `public.profiles` row
- Admin enable/disable now updates `public.profiles.is_active`
- FastAPI startup no longer creates or seeds the SQLite database
- `platform/secrets.toml` is the primary local config for Supabase URL, anon key, service role key, and session secret
- `.env` remains supported for local module URLs and launch commands

New file:

```text
platform/app/core/supabase_client.py
```

Required first admin setup:

```text
Create the admin in Supabase Auth.
Insert a matching row in public.profiles with role = 'admin' and is_active = true.
Then log in through /login using that Supabase Auth email/password.
```

## ATS Backend Integration Status - Completed

Implemented:

- Platform stores the Supabase access token in the server-side session after login
- Student dashboard calls the ATS backend `/api/v1/history` endpoint with the bearer token
- Student dashboard shows ATS API status, latest score, total analyses, and latest resume name
- ATS module detail page shows the same integrated API summary
- Offline or unavailable ATS backend returns a clean status instead of breaking the dashboard

Files:

```text
platform/app/core/ats_integration.py
platform/app/auth/session.py
platform/app/core/users.py
platform/app/routes/dashboard.py
platform/app/routes/modules.py
platform/app/templates/dashboard/dashboard.html
platform/app/templates/modules/module_detail.html
```

Required for live data:

```text
ATS_BACKEND_URL must point to the running ATS FastAPI backend.
The signed-in platform user must also be valid for the ATS backend Supabase JWT verification.
The ATS backend currently reads/writes its history from the `analyses` table used by that module.
```

## Notes-to-Test API Integration Status - Completed

Implemented:

- Platform calls the Notes-to-Test FastAPI backend `/health` endpoint
- Student and Teacher dashboards show Notes-to-Test API status, health, and configured API URL
- Notes-to-Test module detail page shows backend health plus the existing upload, job-status, and quiz-generation endpoint patterns
- Offline or unavailable Notes-to-Test backend returns a clean status instead of breaking the dashboard

Files:

```text
platform/app/core/notes_integration.py
platform/app/routes/dashboard.py
platform/app/routes/modules.py
platform/app/templates/dashboard/dashboard.html
platform/app/templates/modules/module_detail.html
```

Current limitation:

```text
The existing Notes-to-Test backend has upload, job polling, and quiz-generation APIs, but no list/recent-history API yet.
To show real recent documents, recent quizzes, and per-user quiz stats in the platform, add read endpoints to Testmodule later.
```

## Admin Analytics Status - Completed

Implemented:

- Admin dashboard now shows an analytics snapshot
- New admin analytics page at `/admin/analytics`
- Sidebar Analytics link now points to the real admin analytics page
- Analytics cards include total users, students, teachers, module health, ATS analyses, quiz attempts, events, and alumni posts
- Counts are read from Supabase tables where available and module health from configured module URLs

Files:

```text
platform/app/core/analytics.py
platform/app/routes/admin.py
platform/app/routes/dashboard.py
platform/app/templates/admin/analytics.html
platform/app/templates/dashboard/dashboard.html
```

## Events Module Status - Completed

Implemented:

- Real events page at `/events`
- Admin sidebar Events/Seminars link now opens `/events`
- Student sidebar Events link now opens `/events`
- Admin can create events with title, type, start/end time, location, and description
- Student can view events and register
- Registered student state and registration counts are shown on the events page
- Data uses Supabase `events` and `event_registrations` tables

Files:

```text
platform/app/core/events.py
platform/app/routes/events.py
platform/app/templates/events/events.html
platform/app/core/roles.py
platform/app/main.py
```

## Alumni Features Status - Completed

Implemented:

- Real alumni opportunities page at `/alumni/opportunities`
- Student Alumni Connect link now opens `/alumni/opportunities`
- Alumni Student Connect, Chat/Guidance, and Jobs/Internships links now use the real opportunities page
- Alumni can create job, internship, and guidance posts
- Students can browse and filter alumni posts
- Summary cards show job, internship, and guidance post counts
- Data uses Supabase `alumni_posts`

Files:

```text
platform/app/core/alumni.py
platform/app/routes/alumni.py
platform/app/templates/alumni/opportunities.html
platform/app/core/roles.py
platform/app/main.py
```

## Better Module Launcher Status - Completed

Implemented:

- Persistent module process registry at `platform/data/module_processes.json`
- Module status now survives platform server restart if the child PID is still running
- Start logs include timestamp, module key, and command
- Admin module launcher overview page at `/modules`
- Admin sidebar now includes `Module Launcher`
- Launcher page shows module health, process state, command, details, start, stop, and logs actions
- Stopped/exited processes are removed from the registry automatically

Files:

```text
platform/app/core/module_processes.py
platform/app/routes/modules.py
platform/app/templates/modules/module_launcher.html
platform/app/core/roles.py
platform/.env.example
```

Manual note:

```text
Some modules have more than one server. The launcher starts the configured primary command.
For ATS and Notes-to-Test, backend start commands are documented in .env.example for manual use.
```

## Recommended Phase 4

Phase 4 should connect data across modules and add analytics.

Integration tasks:

- Create shared student/teacher identity model
- Map platform users to submodule users
- Add single sign-on style redirects if possible
- Add API proxy routes for modules that expose FastAPI endpoints
- Start API-level integration with ATS and Notes-to-Test because they already have FastAPI backends
- Keep Streamlit/Django modules launched separately until stable

Analytics tasks:

- Attendance analytics cards
- ATS usage stats
- Quiz/test generation stats
- Timetable generation history
- Event participation stats
- Alumni opportunity counts

## Future Work - AI Chatbot and Helpdesk

Requested source/reference project:

```text
https://github.com/Apexcoder1711/AI-powered-attendance-platform.git
Local reference copy: ../TruePresence/AI-powered-attendance-platform
Relevant local files:
  ../TruePresence/AI-powered-attendance-platform/src/voice_rag/
  ../TruePresence/AI-powered-attendance-platform/src/voice_rag/streamlit_ui.py
  ../TruePresence/AI-powered-attendance-platform/src/voice_rag/attendance_context.py
  ../TruePresence/AI-powered-attendance-platform/src/voice_rag/llm.py
```

Do not implement this until the user asks to resume chatbot/helpdesk work.

Planned chatbot requirements:

- Add a platform-native AI chatbot launcher in the right bottom corner of the Smart Campus dashboard.
- Chatbot must work for Student, Teacher, Admin, and Alumni roles.
- Chatbot must respect role hierarchy and RBAC:
  - Student can access only their own profile, attendance, timetable, events, ATS, notes/test, and tickets.
  - Teacher can access only their assigned classes, subjects, students, attendance sessions, timetable, and related tickets.
  - Admin can access campus-wide data, analytics, users, modules, attendance, timetable, events, and helpdesk tickets.
  - Alumni can access only alumni opportunities, their own posts, guidance interactions, and permitted public/student-connect data.
- Reuse the TruePresence Voice-RAG concept, but implement it in FastAPI/Jinja/JS for this platform, not Streamlit UI.
- Use server-side context builders so the model only receives already-authorized data.
- Do not expose passwords, service keys, biometric embeddings, face vectors, voice vectors, or hidden implementation details.
- Add optional AI provider support later using existing local secrets patterns, for example Gemini/OpenAI keys.

Planned authentication enhancement:

- Add Email/OTP authentication as an alternate login method.
- OTP verification must still enforce selected portal role after Supabase verifies the email OTP.
- Keep existing email/password login working.
- Audit OTP request, OTP failure, and OTP login success events.

Planned helpdesk/ticket requirements:

- Add a real Helpdesk section instead of the current placeholder.
- All roles should be able to raise complaints/tickets.
- Ticket categories:
  - WiFi / Internet Issue
  - Hostel Problems
  - Classroom / Lab Issue
  - Library Support
  - IT Support
  - Security / Maintenance
- Ticket fields:
  - Title
  - Description
  - Priority: Low, Medium, High, Urgent
  - Attachment upload: image, PDF, or screenshot
  - Location/building selection
- Store tickets in Supabase, extending `public.helpdesk_tickets` if needed.
- Store uploaded attachments safely with server-side validation and role-checked download routes.
- Ticket visibility rules:
  - Student sees only their own tickets.
  - Teacher sees their own tickets and tickets for their assigned classes if implemented.
  - Alumni sees only their own tickets.
  - Admin sees and manages all tickets.
- Admin should be able to update status: open, in_progress, resolved, closed.

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

The platform now uses Supabase Auth + `profiles` for login and user management.

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

Current Supabase setup progress:

```text
Supabase schema SQL has been run by the user in the Supabase SQL Editor.
platform/secrets.toml.example exists as the safe template.
platform/secrets.toml is the correct local secrets file for this FastAPI platform.
Do not use platform/.streamlit/secrets.toml for the unified platform; that path is only for Streamlit apps/modules.
platform/.gitignore now ignores secrets.toml and .streamlit/secrets.toml.
```

Current local secrets guidance:

```toml
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
anon_key = "YOUR_SUPABASE_ANON_KEY"
service_role_key = "YOUR_SUPABASE_SERVICE_ROLE_KEY"

[app]
session_secret = "replace-with-a-long-random-secret"

[modules]
attendance_url = "http://127.0.0.1:8503"
timetable_url = "http://127.0.0.1:8000"
ats_frontend_url = "http://127.0.0.1:8504"
ats_backend_url = "http://127.0.0.1:8001"
notes_test_url = "http://127.0.0.1:5173"
notes_test_api_url = "http://127.0.0.1:8002"
alumni_url = ""
```

Notes:

```text
Keep alumni_url blank until the alumni module has a real local server URL or deployed URL.
Never paste service_role_key into chat or commit it to GitHub.
Before replacing SQLite auth, create the first admin user in Supabase Auth and insert a matching public.profiles row.
```

## Current Progress - 2026-05-27

Unified platform status:

- Login now uses Supabase Auth.
- User role/status comes from `public.profiles`.
- Admin user management lists Supabase profile users.
- Admin-created users create both Supabase Auth user and `profiles` row.
- Enable/disable updates `profiles.is_active`.
- SQLite auth startup/seed flow has been removed from the platform.

Module status:

- Platform runs at `http://127.0.0.1:9000`.
- Notes-to-Test frontend/API integration is working.
- ATS frontend/API runs, but real scoring still needs `GROQ_API_KEY`.
- Events, admin analytics, modules page, and role-based dashboards are working.
- Timetable module runs at `http://127.0.0.1:8000`.

Attendance-to-Timetable sync:

- Added sync from TruePresence Attendance Supabase tables into AItimetable SQLite.
- Sync reads Attendance `teachers`, `subjects`, and `students`.
- Sync writes timetable `Instructor`, `Course`, `Department`, `Section`, course-instructor links, and `Student`.
- Admin timetable module page has a `Sync Attendance Data` button.
- Last successful sync result:

```text
teachers: 3
subjects: 3
departments: 1
sections: 3
students: 1
```

Verified timetable base data:

```text
teachers: 8
courses: 9
departments: 5
sections: 4
rooms: 5
meeting times: 11
students: 1
```

Verified synced mapping:

```text
CS201 | dsa | sweta singh
```

## Current Progress Update - 2026-05-27

Timetable generation and platform integration were moved forward after the earlier SQLite-based state.

### Timetable Generation Fixes

Implemented:

- Fixed generated timetable display so section IDs are matched correctly.
- Updated AItimetable generation to prioritize section-specific synced courses.
- Added timetable persistence through `TimetableRun` and `TimetableEntry`.
- Added repair logic to prevent real timetable collisions:
  - Same section at same time
  - Same teacher at same time
  - Same room at same time
  - Same subject repeated in the same section on the same day when avoidable
- Changed timetable generation to a full-day schedule model:
  - `9:00 - 10:00`
  - `10:00 - 11:00`
  - `11:00 - 12:00`
  - `12:00 - 12:30` lunch break
  - `12:30 - 1:20`
  - `1:20 - 2:10`
  - `2:10 - 3:00`
- Added AItimetable management command:

```powershell
.\.venv\Scripts\python.exe manage.py seed_full_day_timetable
```

Verified:

```text
Seeded 30 meeting slots and default rooms.
Full-day generation produced 120 entries.
Monday audit: 24 entries, 6 occupied periods per section, lunch break empty.
Section-time collisions: 0
Teacher-time collisions: 0
Room-time collisions: 0
```

### Platform Timetable View

Implemented:

- Added platform timetable page at `/timetable`.
- Platform timetable page is read-only for students and teachers.
- Admin retains generation/sync/open-module controls.
- Teacher access to `/modules/timetable` now redirects to `/timetable`.
- Student and teacher cannot open the raw timetable generator app from platform UI.
- Timetable page now shows one selected day at a time, not the full week.
- Day tabs were added for weekday switching.
- Lunch break row is shown in the platform timetable view.

Role behavior:

```text
Admin: full selected-day timetable.
Student: selected-day timetable for their auto-detected section.
Teacher: selected-day timetable for their auto-detected classes.
```

Auto-detection rules:

```text
Student: platform user email/name matches AItimetable Student email/name.
Teacher: platform user name/email username matches AItimetable Instructor name/uid.
```

Manual mapping fields were removed from Admin User Management.

### Dashboard Improvements

Implemented:

- Student dashboard:
  - Today's timetable
  - Next class
  - Upcoming events count
  - Alumni job/internship counts
- Teacher dashboard:
  - Today's teaching schedule
  - Next class/room
  - Attendance quick link
  - Notes-to-Test quick link
  - Events count
- Admin dashboard:
  - Module health
  - Timetable run count
  - Event registrations
  - Alumni post count

### Supabase Migration for Timetable

The timetable module is now configured to use Supabase Postgres instead of SQLite.

Important:

```text
AItimetable/db.sqlite3 is no longer used by the code after this migration.
AItimetable now requires SUPABASE_DATABASE_URL.
```

Changed:

- Removed SQLite fallback from `AItimetable/Scheduler/settings.py`.
- Fixed `.env` loading so `AItimetable/.env` overrides stale PowerShell environment variables.
- Fixed URL-decoding for database usernames/passwords, so encoded passwords such as `%40` are decoded before psycopg2 connects.
- Added safe `.env.example` format for Supabase pooler connection strings.
- Platform timetable reader now reads Django timetable tables from Supabase REST, not SQLite.
- Platform Attendance-to-Timetable sync now writes to Supabase Django tables, not SQLite.
- Manual Sync Attendance button has been removed from the UI.
- AItimetable generation now auto-imports shared Supabase attendance source tables before generating.
- Shared attendance source table SQL is available at:

```text
platform/supabase/shared_attendance_source.sql
```

Required `AItimetable/.env` format:

```env
SUPABASE_DATABASE_URL=postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
SUPABASE_SSLMODE=require
```

Notes:

```text
Use the Supabase Connect button and copy the Transaction Pooler URI.
Remove square brackets around the password.
Encode special password characters, e.g. @ becomes %40.
Do not commit AItimetable/.env.
```

Completed setup:

```text
manage.py migrate -> successful against Supabase Postgres.
manage.py seed_full_day_timetable -> successful.
Sync Attendance Data -> successful.
Last successful Supabase timetable sync:
teachers: 3
subjects: 3
departments: 1
sections: 3
students: 1
```

### Current Working URLs

```text
Smart Campus platform: http://127.0.0.1:9000
AItimetable Django app: http://127.0.0.1:8000
Platform timetable page: http://127.0.0.1:9000/timetable
Admin timetable module page: http://127.0.0.1:9000/modules/timetable
```

### Next Start Point

Continue from here:

1. Start the platform if needed:

```powershell
cd C:\Users\anike\OneDrive\Desktop\SmartCampus\platform
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

2. Start AItimetable if needed:

```powershell
cd C:\Users\anike\OneDrive\Desktop\SmartCampus\AItimetable
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

3. If Supabase has no timetable seed data:

```powershell
.\.venv\Scripts\python.exe manage.py seed_full_day_timetable
```

4. In platform admin:

```text
/modules/timetable
```

5. In AItimetable:

```text
Generate Timetable
```

6. Verify in platform:

```text
/timetable
```

Next start point:

```text
Open http://127.0.0.1:8000 and generate/check the timetable.
If synced teacher/subject does not appear in generated timetable,
adjust the AItimetable generator view to prioritize attendance-synced sections/courses.
Rooms and meeting times already exist, so only generator selection logic should need checking.
```

## Phase 5 Status - Completed

Phase 5 improves production readiness.

Implemented:

- `.env` is now the primary production config path for Supabase and session settings
- `secrets.toml` remains supported for older local setups
- Production startup validation for required Supabase keys and session secret
- `SESSION_HTTPS_ONLY` support, defaulting to secure cookies in production
- JSONL audit log at `platform/data/audit.log`
- Audit events for login success/failure, logout, admin user creation/status changes, module start/stop, and timetable sync
- Custom 404 and server error pages
- RBAC test coverage under `platform/tests`
- Dockerfile and `docker-compose.yml` for platform deployment
- Supabase migration README
- PowerShell startup scripts:
  - `platform/scripts/start-platform.ps1`
  - `platform/scripts/start-modules.ps1`

Verification:

```text
compileall app tests -> passed
pytest tests -> 3 passed
/login smoke test -> 200 OK
/missing-page smoke test -> 404 OK
```

## Current Progress - 2026-05-28

UI/UX and attendance profile work moved forward.

Implemented:

- Attendance roster lookup now handles section-signature fallback when student section IDs do not match exactly.
- Supabase repair SQL was added for student section/profile mapping cleanup.
- Shared profile photo upload was added for student, teacher, admin, and alumni users.
- Profile photo fallback now generates initials from name, e.g. Ayush Kumar becomes `AK`.
- Topbar profile avatar/upload is available across dashboard roles.
- Dashboard `Signed in as` summary card now shows the current user's profile image or initials.
- Summary cards now get compact related icons automatically.
- Dashboard sidebar now works as a responsive drawer on small screens.
- UI theme was improved toward an Argon-style dashboard:
  - Softer `#f6f9fc` page background
  - White sidebar with active navigation accent
  - Blue/cyan/green dashboard header
  - Tone-based summary-card colors
  - Cleaner shadows, buttons, inputs, tables, badges, and cards
- Future chatbot/helpdesk requirements were documented only. Do not implement them until the user asks to resume that work.

Verification:

```text
compileall app tests -> passed
pytest tests/test_attendance_roster.py tests/test_face_bridge.py tests/test_rbac.py -> 12 passed
/login smoke test on http://127.0.0.1:9000/login -> 200 OK
```

Current local URL:

```text
http://127.0.0.1:9000/login
```

Next start point after login/resume:

```text
1. Open http://127.0.0.1:9000/login.
2. Check dashboard UI on desktop and mobile width.
3. Test profile photo upload for one student, one teacher, one admin, and one alumni account.
4. Create/sign up one new student and verify Supabase stores department, branch, semester, section, academic year, and face profile correctly.
5. Then test teacher attendance roster for that same section.
6. Chatbot/helpdesk is only planned in README for now; start it only when explicitly requested.
```

## Current Progress - Attendance Review, Manual Correction, And Mail - 2026-05-28

Teacher attendance flow was updated to prevent automatic DB saves after photo capture.

Implemented:

- Teacher class photo capture/upload now runs AI face matching first and creates a temporary review only.
- Attendance is saved to Supabase only after the teacher clicks `Confirm and Save Attendance`.
- Alert-style attendance confirmation popup was added on the platform page.
- Popup shows:
  - Total students
  - Present count
  - Absent count
  - AI review count
- Teacher can manually change each student final status between `Present` and `Absent` before confirm.
- Present/Absent counters update live in the popup when teacher changes a dropdown.
- Low-confidence AI matches are shown as AI review, but teacher makes the final Present/Absent decision.
- Manual correction audit is saved in `attendance_audit_logs`.
- Multiple class photos are supported, with AI matches merged across photos.
- Duplicate session prevention was added for teacher + subject + section + date + time slot.
- Student analytics were added:
  - Subject-wise attendance
  - Month-wise attendance
  - Below 75% warning
- Teacher reports were added:
  - Class-wise attendance
  - Low-attendance students
  - Manual correction count
  - CSV export
- TruePresence-style attendance email behavior was ported to the platform:
  - After confirm/save, each student with a valid email gets a background attendance update email.
  - Email logs are written to `email_logs` when the table exists.
  - SMTP settings are documented in `secrets.toml.example`.

Important behavior:

```text
Capture/Upload photo -> AI matching -> Popup review -> Teacher edits Present/Absent -> Confirm and Save -> Supabase records + emails
```

Verification:

```text
.\.venv\Scripts\python.exe -m pytest tests -> 15 passed
.\.venv\Scripts\python.exe -m compileall app -> passed
Updated local server -> http://127.0.0.1:9004
```

Files added/updated for this work:

- `app/core/attendance.py`
- `app/core/attendance_email.py`
- `app/routes/attendance.py`
- `app/templates/attendance/index.html`
- `app/static/js/attendance-review.js`
- `app/static/css/styles.css`
- `supabase/schema.sql`
- `supabase/attendance_review_status.sql`
- `secrets.toml.example`
- `tests/test_attendance_roster.py`

### Supabase Changes Required

Yes, Supabase changes are required if the live database was created before this attendance-review work.

Run this file in Supabase SQL Editor:

```text
platform/supabase/attendance_review_status.sql
```

It applies:

- `attendance_records.status` now allows `needs_review`.
- Unique duplicate-prevention index on `attendance_sessions`:
  - `teacher_id`
  - `subject_id`
  - `section_id`
  - `session_date`
  - `starts_at`
  - `ends_at`
- `email_logs` table for attendance mail tracking.
- Indexes on `email_logs`.

SMTP config is also needed for actual email sending. Add values in `platform/secrets.toml` under `[email]`, for example:

```toml
[email]
smtp_host = "smtp.gmail.com"
smtp_tls_port = "587"
smtp_ssl_port = "465"
smtp_send_mode = "tls"
smtp_user = "your-email@example.com"
smtp_pass = "your-email-app-password"
smtp_from = "your-email@example.com"
smtp_max_retries = "3"
```

## Current Progress - Attendance Popup And Dashboard Polish - 2026-05-28

Attendance UI and dashboard reporting were improved after the first review-popup implementation.

Implemented:

- Old duplicate platform servers on ports `9000` and `9004` were stopped.
- Latest platform server is running on:

```text
http://127.0.0.1:9005/login
```

- Attendance review popup now shows a richer AI summary:
  - Total students
  - Present count
  - Absent count
  - AI review count
  - Roster matches
  - Detected faces
  - AI match rate
- Popup rows now show compact student initials avatars.
- Present students are shown with green styling and a tick mark.
- Absent students are shown with red styling.
- When the teacher manually changes a status, row color updates live:
  - Absent to Present becomes green and stores `Manual Present`
  - Present to Absent becomes red and stores `Manual Absent`
- The earlier optional correction dropdown was removed.
- Manual correction note is now generated automatically and saved in the hidden form field/audit payload.
- Duplicate attendance session warning text is clearer and explains when to update an existing session.
- Teacher confirmation now redirects to the teacher dashboard with an attendance receipt panel.
- Teacher dashboard now shows:
  - Attendance saved receipt after confirm
  - Latest saved attendance
  - Present, absent, and class attendance percent
  - Pending attendance classes for today
  - Saved sessions today
  - Manual correction count
- Student dashboard now shows:
  - Attendance percentage
  - Present count
  - Absent count
  - Below 75% warning
  - Subject-wise attendance cards
  - Recent attendance records
- Timetable entries now include `subject_id` so teacher pending-attendance detection can compare today's timetable against saved attendance sessions.

Files updated:

```text
platform/app/core/attendance.py
platform/app/core/dashboard_summary.py
platform/app/core/timetable_view.py
platform/app/templates/attendance/index.html
platform/app/templates/dashboard/dashboard.html
platform/app/static/js/attendance-review.js
platform/app/static/css/styles.css
platform/tests/test_attendance_roster.py
```

Verification:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_attendance_roster.py tests/test_rbac.py -q -> 9 passed
.\.venv\Scripts\python.exe -m compileall app tests -> passed
/login smoke test on http://127.0.0.1:9005/login -> 200 OK
Only port 9005 is listening for the platform server.
```

Current behavior:

```text
Capture/Upload photo
-> AI face analysis
-> Alert-style review popup
-> Teacher changes Present/Absent if needed
-> Manual note is auto-generated
-> Confirm and Save Attendance
-> Supabase attendance records + audit logs + email dispatch
-> Teacher dashboard receipt and latest attendance summary
```

Next start point:

```text
1. Open http://127.0.0.1:9005/login.
2. Log in as teacher.
3. Open Attendance.
4. Capture/upload a class photo.
5. Confirm the popup appears with green/red rows and automatic manual notes.
6. Confirm and verify the teacher dashboard receipt.
7. Log in as student and verify Attendance Snapshot on the dashboard.
8. Mail setup is planned for later; configure SMTP only when ready.
```

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
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9005
```

Open:

```text
http://127.0.0.1:9005
```
