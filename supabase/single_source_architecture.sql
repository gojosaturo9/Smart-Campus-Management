-- Smart Campus single-source architecture.
-- Run platform/supabase/schema.sql first. This file documents the canonical
-- source and creates read-only compatibility views for legacy modules.

-- Canonical identity:
--   public.profiles           -> every login user: student, teacher, admin, alumni
--   public.teacher_profiles   -> teacher-specific metadata
--   public.student_profiles   -> student-specific metadata
--
-- Canonical academics:
--   public.departments
--   public.sections
--   public.subjects           -> subject ownership via teacher_id -> profiles.id
--   public.subject_sections   -> exact class sections for each subject
--
-- Canonical attendance:
--   public.attendance_students
--   public.attendance_sessions
--   public.attendance_records

drop view if exists public.canonical_teachers;
drop view if exists public.canonical_students;
drop view if exists public.canonical_subjects;

create view public.canonical_teachers as
select
    p.id::text as teacher_id,
    split_part(p.email, '@', 1) as username,
    p.full_name as name,
    p.email as email_id,
    p.email,
    tp.employee_code,
    tp.designation,
    tp.department_id,
    p.is_active,
    p.created_at,
    p.updated_at
from public.profiles p
left join public.teacher_profiles tp on tp.profile_id = p.id
where p.role = 'teacher';

create view public.canonical_students as
select
    p.id::text as student_id,
    sp.roll_number as enrollment_no,
    p.full_name as name,
    p.email as email_id,
    p.email,
    d.name as department,
    d.code as department_code,
    b.name as branch,
    b.code as branch_code,
    s.semester::text as semester,
    s.name as section,
    s.academic_year,
    ats.face_embedding,
    ats.voice_embedding,
    coalesce(ats.biometric_status, 'pending') as biometric_status,
    p.is_active,
    p.created_at,
    p.updated_at
from public.profiles p
join public.student_profiles sp on sp.profile_id = p.id
left join public.sections s on s.id = sp.section_id
left join public.departments d on d.id = s.department_id
left join public.branches b on b.id = s.branch_id
left join public.attendance_students ats on ats.profile_id = p.id
where p.role = 'student';

create view public.canonical_subjects as
select
    s.id::text as subject_id,
    s.code as subject_code,
    s.code as code,
    s.name,
    s.teacher_id::text as teacher_id,
    p.full_name as teacher_name,
    p.email as teacher_email,
    d.name as target_branch,
    array_agg(distinct sec.semester::text) filter (where sec.semester is not null) as target_semester,
    array_agg(distinct sec.name) filter (where sec.name is not null) as target_section,
    s.is_active,
    s.created_at,
    s.updated_at
from public.subjects s
left join public.profiles p on p.id = s.teacher_id
left join public.departments d on d.id = s.department_id
left join public.sections sec on sec.department_id = s.department_id
group by s.id, p.full_name, p.email, d.name;

-- Conservative backfill for older subjects created before subject_sections existed.
-- This only links a subject when its department has exactly one section. If a
-- department has Sem 3 and Sem 6 sections, re-save the subject from
-- /teacher/setup so the exact semester/section is captured.
insert into public.subject_sections (subject_id, section_id)
select s.id, only_section.section_id
from public.subjects s
join (
    select distinct on (department_id)
        department_id,
        id as section_id,
        count(*) over (partition by department_id) as section_count
    from public.sections
    order by department_id, created_at, id
) only_section on only_section.department_id = s.department_id
where only_section.section_count = 1
on conflict (subject_id, section_id) do nothing;

comment on view public.canonical_teachers is
'Read-only compatibility view. Source of truth is profiles + teacher_profiles.';

comment on view public.canonical_students is
'Read-only compatibility view. Source of truth is profiles + student_profiles + attendance_students.';

comment on view public.canonical_subjects is
'Read-only compatibility view. Source of truth is subjects + sections + profiles.';
