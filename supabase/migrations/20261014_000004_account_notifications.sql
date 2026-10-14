create table public.account_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.account_profiles(user_id) on delete cascade,
  kind text not null check (kind = 'account_approved'),
  status text not null default 'pending'
    check (status in ('pending', 'sending', 'sent', 'failed')),
  provider_message_id text,
  failure_code text,
  attempts integer not null default 0 check (attempts >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  sent_at timestamptz
);

create index account_notifications_latest on public.account_notifications(user_id, created_at desc);
alter table public.account_notifications enable row level security;
revoke all on public.account_notifications from anon, authenticated;
grant select, insert, update, delete on public.account_notifications to service_role;

drop function public.set_account_profile_status(uuid, public.account_status);
create function public.set_account_profile_status(
  p_user_id uuid,
  p_status public.account_status
)
returns table (
  previous_status public.account_status,
  user_id uuid,
  email text,
  status public.account_status,
  trial_links_used integer,
  created_at timestamptz,
  approval_notification_id uuid
)
language plpgsql
security definer
set search_path = public
as $$
declare
  old_status public.account_status;
  notification_id uuid;
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

  if p_status = 'approved' and old_status <> 'approved' then
    insert into public.account_notifications(user_id, kind)
    values (p_user_id, 'account_approved')
    returning id into notification_id;
  end if;

  return query
  select old_status, profile.user_id, profile.email, profile.status,
         profile.trial_links_used, profile.created_at, notification_id
  from public.account_profiles as profile
  where profile.user_id = p_user_id;
end;
$$;

create or replace function public.claim_account_notification(p_notification_id uuid)
returns table (id uuid, user_id uuid, email text, attempts integer)
language sql
security definer
set search_path = public
as $$
  update public.account_notifications as notification
  set status = 'sending', attempts = attempts + 1, updated_at = now()
  from public.account_profiles as profile
  where notification.id = p_notification_id
    and notification.user_id = profile.user_id
    and (
      notification.status in ('pending', 'failed')
      or (notification.status = 'sending' and notification.updated_at < now() - interval '5 minutes')
    )
  returning notification.id, notification.user_id, profile.email, notification.attempts;
$$;

create or replace function public.finish_account_notification(
  p_notification_id uuid,
  p_status text,
  p_provider_message_id text,
  p_failure_code text
)
returns setof public.account_notifications
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_status not in ('sent', 'failed') then
    raise exception 'Invalid account notification result';
  end if;

  return query
  update public.account_notifications as notification
  set status = p_status,
      provider_message_id = case when p_status = 'sent' then p_provider_message_id else null end,
      failure_code = case when p_status = 'failed' then p_failure_code else null end,
      sent_at = case when p_status = 'sent' then now() else null end,
      updated_at = now()
  where notification.id = p_notification_id and notification.status = 'sending'
  returning notification.*;
end;
$$;

create or replace function public.list_admin_account_summaries()
returns table (
  user_id uuid,
  email text,
  status public.account_status,
  trial_links_used integer,
  created_at timestamptz,
  approval_email_status text,
  approval_email_failure_code text
)
language sql
security definer
set search_path = public
as $$
  select profile.user_id, profile.email, profile.status, profile.trial_links_used,
         profile.created_at, notification.status, notification.failure_code
  from public.account_profiles as profile
  left join lateral (
    select event.status, event.failure_code
    from public.account_notifications as event
    where event.user_id = profile.user_id and event.kind = 'account_approved'
    order by event.created_at desc
    limit 1
  ) as notification on true
  order by profile.created_at desc;
$$;

revoke execute on function public.set_account_profile_status(uuid, public.account_status)
  from public, anon, authenticated;
grant execute on function public.set_account_profile_status(uuid, public.account_status) to service_role;
revoke execute on function public.claim_account_notification(uuid) from public, anon, authenticated;
grant execute on function public.claim_account_notification(uuid) to service_role;
revoke execute on function public.finish_account_notification(uuid, text, text, text)
  from public, anon, authenticated;
grant execute on function public.finish_account_notification(uuid, text, text, text) to service_role;
revoke execute on function public.list_admin_account_summaries() from public, anon, authenticated;
grant execute on function public.list_admin_account_summaries() to service_role;
