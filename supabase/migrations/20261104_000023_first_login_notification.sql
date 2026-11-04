-- Apply before the matching backend. Existing accounts are not backfilled.
alter table public.account_notifications
  drop constraint account_notifications_kind_check;
alter table public.account_notifications
  add constraint account_notifications_kind_check
  check (kind in ('account_approved', 'account_requested'));

create unique index account_notifications_one_request_per_user
  on public.account_notifications(user_id) where kind = 'account_requested';

create function public.enqueue_new_account_notification()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.account_notifications(user_id, kind)
  values (new.user_id, 'account_requested')
  on conflict (user_id) where kind = 'account_requested' do nothing;
  return new;
end;
$$;
revoke execute on function public.enqueue_new_account_notification() from public, anon, authenticated;

create trigger account_profile_first_login_notification
after insert on public.account_profiles
for each row when (new.status = 'pending')
execute function public.enqueue_new_account_notification();

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

  -- Access changes do not enqueue mail.

  return query
  select old_status, profile.user_id, profile.email, profile.status,
         profile.trial_links_used, profile.created_at, notification_id
  from public.account_profiles as profile
  where profile.user_id = p_user_id;
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
    where event.user_id = profile.user_id and event.kind = 'account_requested'
    order by event.created_at desc
    limit 1
  ) as notification on true
  order by profile.created_at desc;
$$;


-- Retain private notification RPCs and RLS. Legacy approval events are never dispatched
-- by the new backend, which queries only account_requested events.
