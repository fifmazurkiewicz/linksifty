create extension if not exists pgcrypto;

create type public.item_status as enum ('queued', 'processing', 'awaiting_manual_content', 'completed', 'failed');
create type public.input_mode as enum ('fetch', 'paste');
create type public.verdict as enum ('valuable', 'to_review', 'hype');

create table public.settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  valuable_threshold numeric(5,2) not null default 60 check (valuable_threshold between 40 and 100),
  monthly_budget_cents integer not null default 1000 check (monthly_budget_cents >= 0),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.items (
  id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
  original_url text, canonical_url text, input_mode public.input_mode not null, status public.item_status not null default 'queued',
  title text, unread boolean not null default true, failure_reason text, expires_at timestamptz not null default now() + interval '30 days',
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  check ((input_mode = 'fetch' and original_url is not null) or input_mode = 'paste')
);
create table public.source_contents (
  item_id uuid primary key references public.items(id) on delete cascade, user_id uuid not null references auth.users(id) on delete cascade,
  acquisition_method public.input_mode not null, content text not null, content_hash text not null, created_at timestamptz not null default now()
);
create table public.jobs (
  id uuid primary key default gen_random_uuid(), item_id uuid not null unique references public.items(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade, status public.item_status not null default 'queued',
  attempts integer not null default 0 check (attempts between 0 and 2), lease_token uuid, lease_expires_at timestamptz, error_code text, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.assessments (
  id uuid primary key default gen_random_uuid(), item_id uuid not null unique references public.items(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade, note text not null, criteria jsonb not null, score numeric(5,2) not null check (score between 0 and 100),
  verdict public.verdict not null, threshold_snapshot numeric(5,2) not null check (threshold_snapshot between 40 and 100),
  provider_cost_cents integer not null default 0 check (provider_cost_cents >= 0), created_at timestamptz not null default now()
);
create table public.citations (
  id uuid primary key default gen_random_uuid(), assessment_id uuid not null references public.assessments(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade, excerpt text not null, start_position integer not null check (start_position >= 0), end_position integer not null check (end_position >= start_position), source_url text, created_at timestamptz not null default now()
);
create table public.chat_messages (
  id uuid primary key default gen_random_uuid(), item_id uuid not null references public.items(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade, role text not null check (role in ('user', 'assistant')), content text not null,
  citation_ids uuid[] not null default '{}', created_at timestamptz not null default now()
);
create index items_user_order on public.items (user_id, unread desc, created_at desc);
create index jobs_claimable on public.jobs (status, lease_expires_at) where status in ('queued', 'processing');

create or replace function public.claim_next_job(p_user_id uuid)
returns public.jobs language plpgsql security definer set search_path = public as $$
declare claimed public.jobs;
begin
  update public.jobs set status = 'processing', attempts = attempts + 1, lease_token = gen_random_uuid(),
    lease_expires_at = now() + interval '10 minutes', updated_at = now()
  where id = (select id from public.jobs where user_id = p_user_id and (status = 'queued' or (status = 'processing' and lease_expires_at < now())) order by created_at for update skip locked limit 1)
  returning * into claimed;
  return claimed;
end;
$$;

alter table public.settings enable row level security; alter table public.items enable row level security; alter table public.source_contents enable row level security; alter table public.jobs enable row level security; alter table public.assessments enable row level security; alter table public.citations enable row level security; alter table public.chat_messages enable row level security;
create policy "settings owner" on public.settings for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "items owner" on public.items for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "contents owner" on public.source_contents for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "jobs owner" on public.jobs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "assessments owner" on public.assessments for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "citations owner" on public.citations for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "messages owner" on public.chat_messages for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
