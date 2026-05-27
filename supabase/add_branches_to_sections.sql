create table if not exists public.branches (
    id uuid primary key default gen_random_uuid(),
    department_id uuid not null references public.departments(id) on delete cascade,
    name text not null,
    code text not null,
    created_at timestamptz not null default now(),
    unique (department_id, code),
    unique (department_id, name)
);

alter table public.sections
add column if not exists branch_id uuid references public.branches(id) on delete set null;

alter table public.sections
drop constraint if exists sections_department_id_name_semester_academic_year_key;

alter table public.sections
drop constraint if exists sections_department_branch_name_semester_year_key;

drop index if exists public.sections_department_branch_name_semester_year_key;

alter table public.sections
add constraint sections_department_branch_name_semester_year_key
unique (department_id, branch_id, name, semester, academic_year);

create index if not exists idx_branches_department on public.branches(department_id);
create index if not exists idx_sections_branch on public.sections(branch_id);

alter table public.branches enable row level security;

drop policy if exists "branches read authenticated" on public.branches;
create policy "branches read authenticated" on public.branches
for select to authenticated using (true);

drop policy if exists "branches admin all" on public.branches;
create policy "branches admin all" on public.branches
for all to authenticated using (public.is_admin(auth.uid())) with check (public.is_admin(auth.uid()));
