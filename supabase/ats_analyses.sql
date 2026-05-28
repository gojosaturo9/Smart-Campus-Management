create extension if not exists pgcrypto;

create table if not exists public.analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    filename text not null default 'resume',
    ats_score numeric not null default 0,
    keyword_match numeric not null default 0,
    missing_keywords text[] not null default '{}',
    analysis_result jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_analyses_user_created
on public.analyses(user_id, created_at desc);

alter table public.analyses enable row level security;

drop policy if exists "users read own analyses" on public.analyses;
create policy "users read own analyses"
on public.analyses for select
to authenticated
using (user_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "users insert own analyses" on public.analyses;
create policy "users insert own analyses"
on public.analyses for insert
to authenticated
with check (user_id = auth.uid() or public.is_admin(auth.uid()));

drop policy if exists "users delete own analyses" on public.analyses;
create policy "users delete own analyses"
on public.analyses for delete
to authenticated
using (user_id = auth.uid() or public.is_admin(auth.uid()));
