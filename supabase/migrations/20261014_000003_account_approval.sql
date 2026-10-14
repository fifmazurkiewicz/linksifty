create type public.account_status as enum ('pending', 'approved', 'rejected');

create table public.account_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  status public.account_status not null default 'pending',
  trial_links_used integer not null default 0 check (trial_links_used >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.account_profiles enable row level security;
revoke all on public.account_profiles from anon, authenticated;
grant select, insert, update, delete on public.account_profiles to service_role;

create or replace function public.get_or_create_account_profile(
  p_user_id uuid,
  p_email text,
  p_is_admin boolean
)
returns setof public.account_profiles
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_user_id is null or p_email is null or length(trim(p_email)) = 0 then
    raise exception using errcode = 'P0001', message = 'account_profile_missing';
  end if;

  insert into public.account_profiles(user_id, email, status)
  values (
    p_user_id,
    lower(trim(p_email)),
    case when p_is_admin then 'approved'::public.account_status else 'pending'::public.account_status end
  )
  on conflict (user_id) do update
  set email = excluded.email,
      status = case
        when p_is_admin then 'approved'::public.account_status
        else public.account_profiles.status
      end,
      updated_at = now();

  return query
  select * from public.account_profiles where user_id = p_user_id;
end;
$$;

create or replace function public.submit_fetch_items(p_user_id uuid, p_urls text[])
returns setof public.items
language plpgsql
security definer
set search_path = public
as $$
declare
  submitted public.items;
  source_url text;
  current_status public.account_status;
  used_trials integer;
  requested_links integer;
begin
  requested_links := cardinality(p_urls);
  if p_user_id is null or requested_links is null or requested_links not between 1 and 5 then
    raise exception 'A user and one to five URLs are required';
  end if;

  select status, trial_links_used
  into current_status, used_trials
  from public.account_profiles
  where user_id = p_user_id
  for update;

  if not found then
    raise exception using errcode = 'P0001', message = 'account_profile_missing';
  end if;
  if current_status = 'rejected' then
    raise exception using errcode = 'P0001', message = 'account_rejected';
  end if;
  if current_status = 'pending' and used_trials + requested_links > 3 then
    raise exception using errcode = 'P0001', message = 'account_trial_limit_exceeded';
  end if;

  foreach source_url in array p_urls loop
    if source_url is null or source_url !~ '^https?://' then
      raise exception 'Only HTTP and HTTPS URLs are accepted';
    end if;
    insert into public.items(user_id, original_url, canonical_url, input_mode, title)
      values(p_user_id, source_url, source_url, 'fetch', source_url) returning * into submitted;
    insert into public.jobs(user_id, item_id) values(p_user_id, submitted.id);
    return next submitted;
  end loop;

  if current_status = 'pending' then
    update public.account_profiles
    set trial_links_used = used_trials + requested_links, updated_at = now()
    where user_id = p_user_id;
  end if;
end;
$$;

create or replace function public.set_account_profile_status(
  p_user_id uuid,
  p_status public.account_status
)
returns table (
  previous_status public.account_status,
  user_id uuid,
  email text,
  status public.account_status,
  trial_links_used integer,
  created_at timestamptz
)
language plpgsql
security definer
set search_path = public
as $$
declare
  old_status public.account_status;
begin
  if p_status not in ('approved', 'rejected') then
    raise exception 'Only approved or rejected account states can be set';
  end if;

  select profile.status into old_status
  from public.account_profiles as profile
  where profile.user_id = p_user_id
  for update;

  if not found then
    return;
  end if;

  update public.account_profiles as profile
  set status = p_status, updated_at = now()
  where profile.user_id = p_user_id;

  return query
  select old_status, profile.user_id, profile.email, profile.status,
         profile.trial_links_used, profile.created_at
  from public.account_profiles as profile
  where profile.user_id = p_user_id;
end;
$$;

revoke execute on function public.get_or_create_account_profile(uuid, text, boolean)
  from public, anon, authenticated;
grant execute on function public.get_or_create_account_profile(uuid, text, boolean) to service_role;
revoke execute on function public.submit_fetch_items(uuid, text[]) from public, anon, authenticated;
grant execute on function public.submit_fetch_items(uuid, text[]) to service_role;
revoke execute on function public.set_account_profile_status(uuid, public.account_status)
  from public, anon, authenticated;
grant execute on function public.set_account_profile_status(uuid, public.account_status) to service_role;
