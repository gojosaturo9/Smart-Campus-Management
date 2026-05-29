-- Alumni-student mentorship persistence for the unified Smart Campus platform.
-- Run this in Supabase SQL Editor if /alumni/connect reports missing tables.

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

create index if not exists idx_alumni_mentorship_requests_student on public.alumni_mentorship_requests(student_id);
create index if not exists idx_alumni_mentorship_requests_alumni on public.alumni_mentorship_requests(alumni_id);
create index if not exists idx_alumni_mentorship_connections_student on public.alumni_mentorship_connections(student_id);
create index if not exists idx_alumni_mentorship_connections_alumni on public.alumni_mentorship_connections(alumni_id);
create index if not exists idx_alumni_mentorship_messages_connection on public.alumni_mentorship_messages(connection_id);
create index if not exists idx_alumni_mentorship_notifications_user on public.alumni_mentorship_notifications(user_id);

alter table public.alumni_mentorship_requests enable row level security;
alter table public.alumni_mentorship_connections enable row level security;
alter table public.alumni_mentorship_messages enable row level security;
alter table public.alumni_mentorship_notifications enable row level security;

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
