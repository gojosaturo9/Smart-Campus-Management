-- Add teacher-review status support for Smart Campus attendance records.
-- Run this in Supabase SQL Editor if your schema was created before this change.

alter table public.attendance_records
drop constraint if exists attendance_records_status_check;

alter table public.attendance_records
add constraint attendance_records_status_check
check (status in ('present', 'absent', 'needs_review', 'late', 'excused'));

create unique index if not exists idx_attendance_sessions_teacher_class_slot_unique
on public.attendance_sessions (
    teacher_id,
    subject_id,
    section_id,
    session_date,
    coalesce(starts_at, 'epoch'::timestamptz),
    coalesce(ends_at, 'epoch'::timestamptz)
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
