# Codex Resume Log

Last updated: 2026-05-27

## Current Goal

Continue Smart Campus platform work from the student login/signup, face attendance, Supabase branch support, and timetable branch-aware generation changes.

## Current Server

- Platform server should run at `http://127.0.0.1:9000`.
- Start command:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

## Completed Changes

- Student login now has two options:
  - Email/password from the Student Portal box on `/login`.
  - Face login from `/attendance/face-login`.
- Student signup is face-based.
- Unknown face from face login redirects to student signup automatically.
- Signup success logs the student in automatically.
- Face embedding saves to `attendance_students.face_embedding`.
- Face capture UI uses browser `getUserMedia`; no Streamlit.
- Removed `Scan Face`, `Scan Again`, and `Start Camera` controls.
- Capture hides the camera frame during processing to avoid black/frozen preview.
- Global skeleton loading layer added for form submits and internal navigation.
- Student signup fields now include:
  - Full name
  - Email
  - Password
  - Roll number
  - Department
  - Branch
  - Semester
  - Section
  - Academic year
  - Face scan
- Removed phone and admission year from student signup.
- Department and branch are now separate concepts.
- Added branch-aware Supabase migration:
  - `supabase/add_branches_to_sections.sql`
  - `supabase/seed_common_branches.sql`
- Teacher subject setup has branch and branch code fields.
- Timetable generator/view/sync now reads branch-aware section data.

## Supabase State Already Checked

Last read-only DB check showed:

- `branches`: 5
- `sections`: 3
- `sections_with_branch`: 3
- `sections_without_branch`: 0
- `subject_links`: 12

Branches present:

- `CSE`
- `AI-ML`
- `AI-DS`
- `CYBER`
- `DS`

## Important Next Checks

1. Login as teacher from `/login`.
2. Open `/teacher/setup`.
3. Confirm Add Subject form shows:
   - Branch
   - Branch Code
4. Re-save teacher subjects with correct branch values.
5. Login as admin.
6. Generate timetable.
7. Confirm latest timetable labels include branch, for example:

```text
CSE / AI-ML / Sem 6 / A
```

## Files Most Recently Touched

- `app/auth/routes.py`
- `app/routes/attendance.py`
- `app/routes/teacher.py`
- `app/core/attendance.py`
- `app/core/face_bridge.py`
- `app/core/teacher_setup.py`
- `app/core/timetable_generator.py`
- `app/core/timetable_view.py`
- `app/core/timetable_sync.py`
- `app/templates/auth/login.html`
- `app/templates/attendance/face_login.html`
- `app/templates/attendance/signup.html`
- `app/templates/teacher/setup.html`
- `app/templates/base_public.html`
- `app/templates/base_dashboard.html`
- `app/static/css/styles.css`
- `app/static/js/live-face-scan.js`
- `app/static/js/global-loading.js`
- `app/static/js/signup-branch-filter.js`
- `supabase/schema.sql`
- `supabase/add_branches_to_sections.sql`
- `supabase/seed_common_branches.sql`

## Verification Commands

```powershell
python -m compileall app
```

```powershell
.\.venv\Scripts\python.exe -c "from app.core.supabase_client import rest_select; branches=rest_select('branches', {'select':'id,department_id,name,code'}); sections=rest_select('sections', {'select':'id,department_id,branch_id,name,semester,academic_year'}); links=rest_select('subject_sections', {'select':'subject_id,section_id'}); print('branches', len(branches)); print('sections', len(sections)); print('sections_with_branch', sum(1 for s in sections if s.get('branch_id'))); print('sections_without_branch', sum(1 for s in sections if not s.get('branch_id'))); print('subject_links', len(links))"
```

## Notes For Next Codex Session

- Do not switch to Streamlit for the platform.
- Keep FastAPI + HTML/JS.
- User wants AI Attendance-like UX, not exact Streamlit implementation.
- Avoid reintroducing file upload style for face login/signup.
- If timetable does not reflect branch, check whether teacher subjects were re-saved after branch migration.
