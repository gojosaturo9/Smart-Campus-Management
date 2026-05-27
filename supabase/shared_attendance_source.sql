-- DEPRECATED: legacy shared attendance source.
-- Do not use this file for new setup.
-- Use platform/supabase/schema.sql and platform/supabase/single_source_architecture.sql.
-- Canonical source is:
--   profiles, teacher_profiles, student_profiles, departments, sections, subjects.
--
-- This file is kept only for older local experiments that still expect
-- teachers/students text-id tables.

create table if not exists public.teachers (
    teacher_id text primary key,
    username text unique,
    name text not null,
    email text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.subjects (
    subject_id text primary key,
    subject_code text not null,
    name text not null,
    teacher_id text references public.teachers(teacher_id) on delete set null,
    target_branch text,
    target_semester text,
    target_section text,
    max_students int not null default 60,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.subjects add column if not exists subject_code text;
alter table public.subjects add column if not exists subject_id text;
alter table public.subjects add column if not exists name text;
alter table public.subjects add column if not exists teacher_id text;
alter table public.subjects add column if not exists target_branch text;
alter table public.subjects add column if not exists target_semester text;
alter table public.subjects add column if not exists target_section text;
alter table public.subjects add column if not exists max_students int not null default 60;
alter table public.subjects add column if not exists created_at timestamptz not null default now();
alter table public.subjects add column if not exists updated_at timestamptz not null default now();

create table if not exists public.students (
    student_id text primary key,
    enrollment_no text unique,
    name text not null,
    email_id text,
    branch text,
    semester text,
    section text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.teachers add column if not exists username text;
alter table public.teachers add column if not exists teacher_id text;
alter table public.teachers add column if not exists name text;
alter table public.teachers add column if not exists email text;
alter table public.teachers add column if not exists created_at timestamptz not null default now();
alter table public.teachers add column if not exists updated_at timestamptz not null default now();

alter table public.students add column if not exists enrollment_no text;
alter table public.students add column if not exists student_id text;
alter table public.students add column if not exists name text;
alter table public.students add column if not exists email_id text;
alter table public.students add column if not exists branch text;
alter table public.students add column if not exists semester text;
alter table public.students add column if not exists section text;
alter table public.students add column if not exists created_at timestamptz not null default now();
alter table public.students add column if not exists updated_at timestamptz not null default now();

create index if not exists idx_shared_subjects_teacher on public.subjects(teacher_id);
create index if not exists idx_shared_subjects_target on public.subjects(target_branch, target_semester, target_section);
create index if not exists idx_shared_students_class on public.students(branch, semester, section);
