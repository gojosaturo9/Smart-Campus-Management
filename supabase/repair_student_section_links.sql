-- Repair student academic links without deleting Supabase Auth users.
-- Run the SELECT blocks first. Only run the UPDATE blocks after replacing
-- the example email/branch/semester/section values with the student's real data.

-- 1) See what the platform currently resolves for each student.
select
    p.id as profile_id,
    p.email,
    p.full_name,
    sp.roll_number,
    d.name as department,
    d.code as department_code,
    b.name as branch,
    b.code as branch_code,
    s.semester,
    s.name as section,
    s.academic_year,
    ats.biometric_status,
    ats.face_embedding is not null as has_face_profile
from public.profiles p
left join public.student_profiles sp on sp.profile_id = p.id
left join public.sections s on s.id = sp.section_id
left join public.departments d on d.id = s.department_id
left join public.branches b on b.id = s.branch_id
left join public.attendance_students ats on ats.profile_id = p.id
where p.role = 'student'
order by p.created_at desc;

-- 2) Find broken student rows.
select
    p.email,
    sp.roll_number,
    sp.section_id as student_profile_section_id,
    ats.section_id as attendance_student_section_id,
    s.department_id,
    s.branch_id,
    s.semester,
    s.name as section,
    s.academic_year,
    ats.biometric_status,
    ats.face_embedding is not null as has_face_profile
from public.profiles p
left join public.student_profiles sp on sp.profile_id = p.id
left join public.attendance_students ats on ats.profile_id = p.id
left join public.sections s on s.id = coalesce(sp.section_id, ats.section_id)
where p.role = 'student'
  and (
      sp.section_id is null
      or ats.section_id is null
      or sp.section_id is distinct from ats.section_id
      or s.department_id is null
      or s.branch_id is null
      or s.semester is null
      or s.name is null
      or s.academic_year is null
      or ats.biometric_status is distinct from 'verified'
      or ats.face_embedding is null
  )
order by p.created_at desc;

-- 3) Example repair for ONE student.
-- Replace these values, then run the block.
-- This version creates the target section if it does not already exist.
--
-- with repair_input as (
--     select
--         'student@example.com'::text as email,
--         'CSE'::text as department_code,
--         'CSE'::text as branch_code,
--         3::int as semester,
--         'A'::text as section_name,
--         '2026-27'::text as academic_year
-- ),
-- target_department as (
--     select d.id
--     from public.departments d
--     join repair_input r on r.department_code = d.code
--     limit 1
-- ),
-- target_branch as (
--     select b.id
--     from public.branches b
--     join target_department d on d.id = b.department_id
--     join repair_input r on r.branch_code = b.code
--     limit 1
-- ),
-- ensured_section as (
--     insert into public.sections (department_id, branch_id, name, semester, academic_year)
--     select d.id, b.id, r.section_name, r.semester, r.academic_year
--     from repair_input r
--     join target_department d on true
--     join target_branch b on true
--     on conflict (department_id, branch_id, name, semester, academic_year)
--     do update set name = excluded.name
--     returning id
-- ),
-- target_section as (
--     select id from ensured_section
-- ),
-- target_student as (
--     select p.id
--     from public.profiles p
--     join repair_input r on r.email = p.email
--     where p.role = 'student'
--     limit 1
-- ),
-- updated_student_profile as (
--     update public.student_profiles sp
--     set section_id = target_section.id
--     from target_student, target_section
--     where sp.profile_id = target_student.id
--     returning sp.profile_id
-- )
-- update public.attendance_students ats
-- set section_id = target_section.id,
--     biometric_status = case
--         when ats.face_embedding is not null then 'verified'
--         else ats.biometric_status
--     end
-- from target_student, target_section
-- where ats.profile_id = target_student.id;
--
-- 4) If the UPDATE affects 0 rows, check whether department/branch codes exist:
--
-- select d.code as department_code, d.name as department, b.code as branch_code, b.name as branch
-- from public.departments d
-- left join public.branches b on b.department_id = d.id
-- order by d.code, b.code;
