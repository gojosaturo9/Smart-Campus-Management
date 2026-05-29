-- Smart Campus Management Platform - Supabase schema
-- Run this file in the Supabase SQL Editor.
-- This schema assumes Supabase Auth is the source of login identities.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Shared helpers
-- ---------------------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Core identity and campus structure
-- ---------------------------------------------------------------------------

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text not null,
    email text not null unique,
    role text not null check (role in ('student', 'teacher', 'admin', 'alumni')),
    avatar_url text,
    phone text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create or replace function public.is_admin(user_id uuid)
returns boolean
language sql
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.profiles
        where id = user_id
          and role = 'admin'
          and is_active = true
    );
$$;

create table if not exists public.departments (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    code text not null unique,
    created_at timestamptz not null default now()
);

create table if not exists public.branches (
    id uuid primary key default gen_random_uuid(),
    department_id uuid not null references public.departments(id) on delete cascade,
    name text not null,
    code text not null,
    created_at timestamptz not null default now(),
    unique (department_id, code),
    unique (department_id, name)
);

create table if not exists public.sections (
    id uuid primary key default gen_random_uuid(),
    department_id uuid references public.departments(id) on delete set null,
    branch_id uuid references public.branches(id) on delete set null,
    name text not null,
    semester int,
    academic_year text,
    created_at timestamptz not null default now(),
    unique (department_id, branch_id, name, semester, academic_year)
);

create table if not exists public.subjects (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    department_id uuid references public.departments(id) on delete set null,
    teacher_id uuid references public.profiles(id) on delete set null,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists subjects_set_updated_at on public.subjects;
create trigger subjects_set_updated_at
before update on public.subjects
for each row execute function public.set_updated_at();

create table if not exists public.subject_sections (
    id uuid primary key default gen_random_uuid(),
    subject_id uuid not null references public.subjects(id) on delete cascade,
    section_id uuid not null references public.sections(id) on delete cascade,
    created_at timestamptz not null default now(),
    unique (subject_id, section_id)
);

create table if not exists public.student_profiles (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    roll_number text not null unique,
    section_id uuid references public.sections(id) on delete set null,
    admission_year int,
    created_at timestamptz not null default now()
);

create table if not exists public.teacher_profiles (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    employee_code text unique,
    department_id uuid references public.departments(id) on delete set null,
    designation text,
    created_at timestamptz not null default now()
);

create table if not exists public.admin_profiles (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    designation text,
    created_at timestamptz not null default now()
);

create table if not exists public.alumni_profiles (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    graduation_year int,
    company text,
    job_title text,
    linkedin_url text,
    bio text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists alumni_profiles_set_updated_at on public.alumni_profiles;
create trigger alumni_profiles_set_updated_at
before update on public.alumni_profiles
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- AI Attendance / TruePresence
-- ---------------------------------------------------------------------------

create table if not exists public.attendance_students (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null unique references public.profiles(id) on delete cascade,
    roll_number text not null unique,
    section_id uuid references public.sections(id) on delete set null,
    face_embedding jsonb,
    voice_embedding jsonb,
    biometric_status text not null default 'pending'
        check (biometric_status in ('pending', 'verified', 'rejected')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists attendance_students_set_updated_at on public.attendance_students;
create trigger attendance_students_set_updated_at
before update on public.attendance_students
for each row execute function public.set_updated_at();

create table if not exists public.attendance_sessions (
    id uuid primary key default gen_random_uuid(),
    subject_id uuid references public.subjects(id) on delete set null,
    teacher_id uuid references public.profiles(id) on delete set null,
    section_id uuid references public.sections(id) on delete set null,
    session_date date not null,
    starts_at timestamptz,
    ends_at timestamptz,
    status text not null default 'open'
        check (status in ('open', 'closed', 'cancelled')),
    created_at timestamptz not null default now()
);

create unique index if not exists idx_attendance_sessions_teacher_class_slot_unique
on public.attendance_sessions (
    teacher_id,
    subject_id,
    section_id,
    session_date,
    coalesce(starts_at, 'epoch'::timestamptz),
    coalesce(ends_at, 'epoch'::timestamptz)
);

create table if not exists public.attendance_records (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references public.attendance_sessions(id) on delete cascade,
    student_id uuid not null references public.attendance_students(id) on delete cascade,
    status text not null check (status in ('present', 'absent', 'needs_review', 'late', 'excused')),
    confidence numeric(6, 4),
    liveness_passed boolean,
    marked_at timestamptz not null default now(),
    unique (session_id, student_id)
);

alter table public.attendance_records
drop constraint if exists attendance_records_status_check;

alter table public.attendance_records
add constraint attendance_records_status_check
check (status in ('present', 'absent', 'needs_review', 'late', 'excused'));

create table if not exists public.attendance_audit_logs (
    id uuid primary key default gen_random_uuid(),
    record_id uuid references public.attendance_records(id) on delete cascade,
    action text not null,
    actor_id uuid references public.profiles(id) on delete set null,
    old_value jsonb,
    new_value jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.email_logs (
    id uuid primary key default gen_random_uuid(),
    student_id uuid references public.attendance_students(id) on delete set null,
    to_email text not null,
    email_type text not null default 'attendance_update',
    status text not null default 'queued',
    subject text,
    body_preview text,
    error_message text,
    attempt_count integer not null default 0,
    created_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_email_logs_student_id on public.email_logs(student_id);
create index if not exists idx_email_logs_status on public.email_logs(status);
create index if not exists idx_email_logs_created_at on public.email_logs(created_at desc);

-- ---------------------------------------------------------------------------
-- AI Timetable
-- ---------------------------------------------------------------------------

create table if not exists public.timetable_rooms (
    id uuid primary key default gen_random_uuid(),
    room_number text not null unique,
    seating_capacity int not null default 0 check (seating_capacity >= 0),
    created_at timestamptz not null default now()
);

create table if not exists public.timetable_time_slots (
    id uuid primary key default gen_random_uuid(),
    day text not null check (day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time time not null,
    end_time time not null,
    label text not null,
    unique (day, start_time, end_time)
);

create table if not exists public.timetable_courses (
    id uuid primary key default gen_random_uuid(),
    course_code text not null unique,
    course_name text not null,
    max_students int not null default 0 check (max_students >= 0),
    department_id uuid references public.departments(id) on delete set null,
    created_at timestamptz not null default now()
);

create table if not exists public.timetable_course_teachers (
    id uuid primary key default gen_random_uuid(),
    course_id uuid not null references public.timetable_courses(id) on delete cascade,
    teacher_id uuid not null references public.profiles(id) on delete cascade,
    unique (course_id, teacher_id)
);

create table if not exists public.timetable_runs (
    id uuid primary key default gen_random_uuid(),
    scope text not null default 'week' check (scope in ('day', 'week')),
    generated_by uuid references public.profiles(id) on delete set null,
    algorithm_meta jsonb not null default '{}'::jsonb,
    generated_at timestamptz not null default now()
);

create table if not exists public.timetable_entries (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references public.timetable_runs(id) on delete cascade,
    subject_id uuid references public.subjects(id) on delete set null,
    section_id uuid references public.sections(id) on delete set null,
    teacher_id uuid references public.profiles(id) on delete set null,
    room_id uuid references public.timetable_rooms(id) on delete set null,
    time_slot_id uuid references public.timetable_time_slots(id) on delete set null,
    day text not null,
    created_at timestamptz not null default now(),
    unique (run_id, section_id, day, time_slot_id),
    unique (run_id, teacher_id, day, time_slot_id),
    unique (run_id, room_id, day, time_slot_id)
);

create table if not exists public.timetable_notifications (
    id uuid primary key default gen_random_uuid(),
    student_id uuid references public.profiles(id) on delete cascade,
    timetable_entry_id uuid references public.timetable_entries(id) on delete cascade,
    title text not null,
    message text not null,
    is_sent boolean not null default false,
    created_at timestamptz not null default now(),
    sent_at timestamptz
);

-- ---------------------------------------------------------------------------
-- AI ATS Resume Scorer
-- ---------------------------------------------------------------------------

create table if not exists public.ats_resumes (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    file_name text not null,
    file_url text,
    parsed_text text,
    uploaded_at timestamptz not null default now()
);

create table if not exists public.ats_job_descriptions (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    title text not null,
    company text,
    description text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.ats_analyses (
    id uuid primary key default gen_random_uuid(),
    resume_id uuid references public.ats_resumes(id) on delete cascade,
    job_description_id uuid references public.ats_job_descriptions(id) on delete cascade,
    student_id uuid not null references public.profiles(id) on delete cascade,
    overall_score numeric(5, 2),
    keyword_score numeric(5, 2),
    formatting_score numeric(5, 2),
    content_score numeric(5, 2),
    skills_score numeric(5, 2),
    ats_compatibility_score numeric(5, 2),
    suggestions jsonb not null default '[]'::jsonb,
    missing_keywords jsonb not null default '[]'::jsonb,
    matched_keywords jsonb not null default '[]'::jsonb,
    report_url text,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- AI Notes-to-Test Generator
-- ---------------------------------------------------------------------------

create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid references public.profiles(id) on delete set null,
    title text,
    author text,
    file_type text,
    file_url text,
    document_hash text unique,
    meta jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.chapters (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references public.documents(id) on delete cascade,
    chapter_title text,
    content text,
    chapter_hash text unique,
    created_at timestamptz not null default now()
);

create table if not exists public.questions (
    id uuid primary key default gen_random_uuid(),
    chapter_id uuid not null references public.chapters(id) on delete cascade,
    question_text text not null,
    answer_text text,
    question_type text,
    difficulty text,
    options jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.quiz_attempts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    chapter_id uuid references public.chapters(id) on delete set null,
    score numeric(6, 2),
    total_questions int not null default 0,
    answers jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Events / seminars
-- ---------------------------------------------------------------------------

create table if not exists public.events (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    description text,
    event_type text,
    starts_at timestamptz,
    ends_at timestamptz,
    location text,
    created_by uuid references public.profiles(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists events_set_updated_at on public.events;
create trigger events_set_updated_at
before update on public.events
for each row execute function public.set_updated_at();

create table if not exists public.event_registrations (
    id uuid primary key default gen_random_uuid(),
    event_id uuid not null references public.events(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    status text not null default 'registered'
        check (status in ('registered', 'cancelled', 'attended')),
    registered_at timestamptz not null default now(),
    unique (event_id, user_id)
);

-- ---------------------------------------------------------------------------
-- Alumni connection
-- ---------------------------------------------------------------------------

create table if not exists public.alumni_posts (
    id uuid primary key default gen_random_uuid(),
    alumni_id uuid not null references public.profiles(id) on delete cascade,
    post_type text not null check (post_type in ('job', 'internship', 'guidance')),
    title text not null,
    description text,
    company text,
    apply_url text,
    expires_at timestamptz,
    created_at timestamptz not null default now()
);

create table if not exists public.alumni_messages (
    id uuid primary key default gen_random_uuid(),
    sender_id uuid not null references public.profiles(id) on delete cascade,
    receiver_id uuid not null references public.profiles(id) on delete cascade,
    message text not null,
    created_at timestamptz not null default now(),
    read_at timestamptz
);

create table if not exists public.alumni_mentorship_requests (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    alumni_id uuid not null references public.profiles(id) on delete cascade,
    intent text not null,
    message text not null,
    status text not null default 'pending'
        check (status in ('pending', 'accepted', 'rejected', 'cancelled')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists alumni_mentorship_requests_set_updated_at on public.alumni_mentorship_requests;
create trigger alumni_mentorship_requests_set_updated_at
before update on public.alumni_mentorship_requests
for each row execute function public.set_updated_at();

create table if not exists public.alumni_mentorship_connections (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    alumni_id uuid not null references public.profiles(id) on delete cascade,
    request_id uuid references public.alumni_mentorship_requests(id) on delete set null,
    status text not null default 'active'
        check (status in ('active', 'closed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists alumni_mentorship_connections_set_updated_at on public.alumni_mentorship_connections;
create trigger alumni_mentorship_connections_set_updated_at
before update on public.alumni_mentorship_connections
for each row execute function public.set_updated_at();

create unique index if not exists idx_alumni_mentorship_active_pair
on public.alumni_mentorship_connections(student_id, alumni_id)
where status = 'active';

create table if not exists public.alumni_mentorship_messages (
    id uuid primary key default gen_random_uuid(),
    connection_id uuid not null references public.alumni_mentorship_connections(id) on delete cascade,
    sender_id uuid not null references public.profiles(id) on delete cascade,
    message text not null,
    created_at timestamptz not null default now(),
    read_at timestamptz
);

create table if not exists public.alumni_mentorship_notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    title text not null,
    body text,
    is_read boolean not null default false,
    related_connection_id uuid references public.alumni_mentorship_connections(id) on delete cascade,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Helpdesk and classroom placeholders
-- ---------------------------------------------------------------------------

create table if not exists public.helpdesk_tickets (
    id uuid primary key default gen_random_uuid(),
    created_by uuid not null references public.profiles(id) on delete cascade,
    assigned_to uuid references public.profiles(id) on delete set null,
    title text not null,
    description text,
    status text not null default 'open'
        check (status in ('open', 'in_progress', 'resolved', 'closed')),
    priority text not null default 'normal'
        check (priority in ('low', 'normal', 'high', 'urgent')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists helpdesk_tickets_set_updated_at on public.helpdesk_tickets;
create trigger helpdesk_tickets_set_updated_at
before update on public.helpdesk_tickets
for each row execute function public.set_updated_at();

create table if not exists public.classroom_announcements (
    id uuid primary key default gen_random_uuid(),
    teacher_id uuid not null references public.profiles(id) on delete cascade,
    section_id uuid references public.sections(id) on delete set null,
    subject_id uuid references public.subjects(id) on delete set null,
    title text not null,
    body text,
    attachment_url text,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Platform module registry
-- ---------------------------------------------------------------------------

create table if not exists public.platform_modules (
    id uuid primary key default gen_random_uuid(),
    module_key text not null unique,
    name text not null,
    launch_url text,
    health_status text not null default 'unknown',
    last_checked_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_platform_modules_module_key_unique
on public.platform_modules (module_key);

drop trigger if exists platform_modules_set_updated_at on public.platform_modules;
create trigger platform_modules_set_updated_at
before update on public.platform_modules
for each row execute function public.set_updated_at();

insert into public.platform_modules (module_key, name, launch_url)
values
    ('attendance', 'AI Attendance System', 'http://127.0.0.1:8503'),
    ('timetable', 'AI Timetable Generator', 'http://127.0.0.1:8000'),
    ('ats-resume', 'AI ATS Resume Scorer', 'http://127.0.0.1:8504'),
    ('notes-to-test', 'AI Notes-to-Test Generator', 'http://127.0.0.1:5173'),
    ('alumni-connect', 'Alumni Connection', null)
on conflict (module_key) do nothing;

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

create index if not exists idx_profiles_role on public.profiles(role);
create index if not exists idx_profiles_active on public.profiles(is_active);
create index if not exists idx_subjects_teacher on public.subjects(teacher_id);
create index if not exists idx_attendance_sessions_teacher on public.attendance_sessions(teacher_id);
create index if not exists idx_attendance_sessions_section on public.attendance_sessions(section_id);
create index if not exists idx_attendance_records_session on public.attendance_records(session_id);
create index if not exists idx_timetable_entries_run on public.timetable_entries(run_id);
create index if not exists idx_timetable_entries_teacher on public.timetable_entries(teacher_id);
create index if not exists idx_ats_analyses_student on public.ats_analyses(student_id);
create index if not exists idx_documents_owner on public.documents(owner_id);
create index if not exists idx_quiz_attempts_student on public.quiz_attempts(student_id);
create index if not exists idx_alumni_posts_type on public.alumni_posts(post_type);
create index if not exists idx_alumni_messages_receiver on public.alumni_messages(receiver_id);
create index if not exists idx_alumni_mentorship_requests_student on public.alumni_mentorship_requests(student_id);
create index if not exists idx_alumni_mentorship_requests_alumni on public.alumni_mentorship_requests(alumni_id);
create index if not exists idx_alumni_mentorship_connections_student on public.alumni_mentorship_connections(student_id);
create index if not exists idx_alumni_mentorship_connections_alumni on public.alumni_mentorship_connections(alumni_id);
create index if not exists idx_alumni_mentorship_messages_connection on public.alumni_mentorship_messages(connection_id);
create index if not exists idx_alumni_mentorship_notifications_user on public.alumni_mentorship_notifications(user_id);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.profiles enable row level security;
alter table public.departments enable row level security;
alter table public.branches enable row level security;
alter table public.sections enable row level security;
alter table public.subjects enable row level security;
alter table public.subject_sections enable row level security;
alter table public.student_profiles enable row level security;
alter table public.teacher_profiles enable row level security;
alter table public.admin_profiles enable row level security;
alter table public.alumni_profiles enable row level security;
alter table public.attendance_students enable row level security;
alter table public.attendance_sessions enable row level security;
alter table public.attendance_records enable row level security;
alter table public.attendance_audit_logs enable row level security;
alter table public.timetable_rooms enable row level security;
alter table public.timetable_time_slots enable row level security;
alter table public.timetable_courses enable row level security;
alter table public.timetable_course_teachers enable row level security;
alter table public.timetable_runs enable row level security;
alter table public.timetable_entries enable row level security;
alter table public.timetable_notifications enable row level security;
alter table public.ats_resumes enable row level security;
alter table public.ats_job_descriptions enable row level security;
alter table public.ats_analyses enable row level security;
alter table public.documents enable row level security;
alter table public.chapters enable row level security;
alter table public.questions enable row level security;
alter table public.quiz_attempts enable row level security;
alter table public.events enable row level security;
alter table public.event_registrations enable row level security;
alter table public.alumni_posts enable row level security;
alter table public.alumni_messages enable row level security;
alter table public.alumni_mentorship_requests enable row level security;
alter table public.alumni_mentorship_connections enable row level security;
alter table public.alumni_mentorship_messages enable row level security;
alter table public.alumni_mentorship_notifications enable row level security;
alter table public.helpdesk_tickets enable row level security;
alter table public.classroom_announcements enable row level security;
alter table public.platform_modules enable row level security;

-- Simple baseline policies for the unified platform.
-- The FastAPI platform should use the service role key for admin/server actions.
-- Authenticated users get self-service access where appropriate.

drop policy if exists "profiles self read" on public.profiles;
create policy "profiles self read"
on public.profiles for select
to authenticated
using (id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "profiles self update" on public.profiles;
create policy "profiles self update"
on public.profiles for update
to authenticated
using (id = auth.uid() or public.is_admin(auth.uid()))
with check (id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "admins manage profiles" on public.profiles;
create policy "admins manage profiles"
on public.profiles for all
to authenticated
using (public.is_admin(auth.uid()))
with check (public.is_admin(auth.uid()));

drop policy if exists "campus reference read" on public.departments;
create policy "campus reference read" on public.departments for select to authenticated using (true);
drop policy if exists "campus branches read" on public.branches;
create policy "campus branches read" on public.branches for select to authenticated using (true);
drop policy if exists "campus sections read" on public.sections;
create policy "campus sections read" on public.sections for select to authenticated using (true);
drop policy if exists "campus subjects read" on public.subjects;
create policy "campus subjects read" on public.subjects for select to authenticated using (true);
drop policy if exists "campus subject sections read" on public.subject_sections;
create policy "campus subject sections read" on public.subject_sections for select to authenticated using (true);

drop policy if exists "admins manage departments" on public.departments;
create policy "admins manage departments" on public.departments for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage branches" on public.branches;
create policy "admins manage branches" on public.branches for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage sections" on public.sections;
create policy "admins manage sections" on public.sections for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage subjects" on public.subjects;
create policy "admins manage subjects" on public.subjects for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage subject sections" on public.subject_sections;
create policy "admins manage subject sections" on public.subject_sections for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));

drop policy if exists "own student profile read" on public.student_profiles;
create policy "own student profile read" on public.student_profiles for select to authenticated using (profile_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "own teacher profile read" on public.teacher_profiles;
create policy "own teacher profile read" on public.teacher_profiles for select to authenticated using (profile_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "own admin profile read" on public.admin_profiles;
create policy "own admin profile read" on public.admin_profiles for select to authenticated using (profile_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "alumni profile read" on public.alumni_profiles;
create policy "alumni profile read" on public.alumni_profiles for select to authenticated using (true);

drop policy if exists "admins manage student profiles" on public.student_profiles;
create policy "admins manage student profiles" on public.student_profiles for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage teacher profiles" on public.teacher_profiles;
create policy "admins manage teacher profiles" on public.teacher_profiles for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage admin profiles" on public.admin_profiles;
create policy "admins manage admin profiles" on public.admin_profiles for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));

drop policy if exists "attendance students self read" on public.attendance_students;
create policy "attendance students self read" on public.attendance_students for select to authenticated using (profile_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "attendance sessions read" on public.attendance_sessions;
create policy "attendance sessions read" on public.attendance_sessions for select to authenticated using (true);
drop policy if exists "attendance records read" on public.attendance_records;
create policy "attendance records read" on public.attendance_records for select to authenticated using (true);

drop policy if exists "teachers admins manage attendance sessions" on public.attendance_sessions;
create policy "teachers admins manage attendance sessions"
on public.attendance_sessions for all to authenticated
using (teacher_id = auth.uid() or public.is_admin(auth.uid()))
with check (teacher_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "teachers admins manage attendance records" on public.attendance_records;
create policy "teachers admins manage attendance records"
on public.attendance_records for all to authenticated
using (public.is_admin(auth.uid()) or exists (
    select 1 from public.attendance_sessions s
    where s.id = attendance_records.session_id
      and s.teacher_id = auth.uid()
))
with check (public.is_admin(auth.uid()) or exists (
    select 1 from public.attendance_sessions s
    where s.id = attendance_records.session_id
      and s.teacher_id = auth.uid()
));

drop policy if exists "timetable read" on public.timetable_entries;
create policy "timetable read" on public.timetable_entries for select to authenticated using (true);
drop policy if exists "timetable runs read" on public.timetable_runs;
create policy "timetable runs read" on public.timetable_runs for select to authenticated using (true);
drop policy if exists "admins manage timetable runs" on public.timetable_runs;
create policy "admins manage timetable runs" on public.timetable_runs for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "admins manage timetable entries" on public.timetable_entries;
create policy "admins manage timetable entries" on public.timetable_entries for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));

drop policy if exists "student ats read" on public.ats_resumes;
create policy "student ats read" on public.ats_resumes for select to authenticated using (student_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "student ats manage resumes" on public.ats_resumes;
create policy "student ats manage resumes" on public.ats_resumes for all to authenticated using (student_id = auth.uid() or public.is_admin(auth.uid())) with check (student_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "student ats manage jd" on public.ats_job_descriptions;
create policy "student ats manage jd" on public.ats_job_descriptions for all to authenticated using (student_id = auth.uid() or public.is_admin(auth.uid())) with check (student_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "student ats manage analyses" on public.ats_analyses;
create policy "student ats manage analyses" on public.ats_analyses for all to authenticated using (student_id = auth.uid() or public.is_admin(auth.uid())) with check (student_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "documents owner access" on public.documents;
create policy "documents owner access" on public.documents for all to authenticated using (owner_id = auth.uid() or public.is_admin(auth.uid())) with check (owner_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "chapters authenticated read" on public.chapters;
create policy "chapters authenticated read" on public.chapters for select to authenticated using (true);
drop policy if exists "questions authenticated read" on public.questions;
create policy "questions authenticated read" on public.questions for select to authenticated using (true);
drop policy if exists "quiz attempts owner access" on public.quiz_attempts;
create policy "quiz attempts owner access" on public.quiz_attempts for all to authenticated using (student_id = auth.uid() or public.is_admin(auth.uid())) with check (student_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "events read" on public.events;
create policy "events read" on public.events for select to authenticated using (true);
drop policy if exists "admins manage events" on public.events;
create policy "admins manage events" on public.events for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
drop policy if exists "event registrations own" on public.event_registrations;
create policy "event registrations own" on public.event_registrations for all to authenticated using (user_id = auth.uid() or public.is_admin(auth.uid())) with check (user_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "alumni posts read" on public.alumni_posts;
create policy "alumni posts read" on public.alumni_posts for select to authenticated using (true);
drop policy if exists "alumni manage own posts" on public.alumni_posts;
create policy "alumni manage own posts" on public.alumni_posts for all to authenticated using (alumni_id = auth.uid() or public.is_admin(auth.uid())) with check (alumni_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "messages participants read" on public.alumni_messages;
create policy "messages participants read" on public.alumni_messages for select to authenticated using (sender_id = auth.uid() or receiver_id = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "messages sender insert" on public.alumni_messages;
create policy "messages sender insert" on public.alumni_messages for insert to authenticated with check (sender_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "mentorship requests participants" on public.alumni_mentorship_requests;
create policy "mentorship requests participants"
on public.alumni_mentorship_requests for all
to authenticated
using (student_id = auth.uid() or alumni_id = auth.uid() or public.is_admin(auth.uid()))
with check (student_id = auth.uid() or alumni_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "mentorship connections participants" on public.alumni_mentorship_connections;
create policy "mentorship connections participants"
on public.alumni_mentorship_connections for all
to authenticated
using (student_id = auth.uid() or alumni_id = auth.uid() or public.is_admin(auth.uid()))
with check (student_id = auth.uid() or alumni_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "mentorship messages participants" on public.alumni_mentorship_messages;
create policy "mentorship messages participants"
on public.alumni_mentorship_messages for all
to authenticated
using (
    public.is_admin(auth.uid()) or exists (
        select 1 from public.alumni_mentorship_connections c
        where c.id = alumni_mentorship_messages.connection_id
          and (c.student_id = auth.uid() or c.alumni_id = auth.uid())
    )
)
with check (
    sender_id = auth.uid() and exists (
        select 1 from public.alumni_mentorship_connections c
        where c.id = alumni_mentorship_messages.connection_id
          and (c.student_id = auth.uid() or c.alumni_id = auth.uid())
    )
);

drop policy if exists "mentorship notifications owner" on public.alumni_mentorship_notifications;
create policy "mentorship notifications owner"
on public.alumni_mentorship_notifications for all
to authenticated
using (user_id = auth.uid() or public.is_admin(auth.uid()))
with check (user_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "helpdesk own read" on public.helpdesk_tickets;
create policy "helpdesk own read" on public.helpdesk_tickets for select to authenticated using (created_by = auth.uid() or assigned_to = auth.uid() or public.is_admin(auth.uid()));
drop policy if exists "helpdesk own create" on public.helpdesk_tickets;
create policy "helpdesk own create" on public.helpdesk_tickets for insert to authenticated with check (created_by = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "classroom announcements read" on public.classroom_announcements;
create policy "classroom announcements read" on public.classroom_announcements for select to authenticated using (true);
drop policy if exists "teachers admins manage classroom announcements" on public.classroom_announcements;
create policy "teachers admins manage classroom announcements" on public.classroom_announcements for all to authenticated using (teacher_id = auth.uid() or public.is_admin(auth.uid())) with check (teacher_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "platform modules read" on public.platform_modules;
create policy "platform modules read" on public.platform_modules for select to authenticated using (true);
drop policy if exists "admins manage platform modules" on public.platform_modules;
create policy "admins manage platform modules" on public.platform_modules for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
