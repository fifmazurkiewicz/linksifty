-- Apply before the matching backend. A blocked user may re-request access; each request is a
-- new notification event, but at most one unfinished request exists per user.
drop index public.account_notifications_one_request_per_user;
create unique index account_notifications_one_open_request_per_user
  on public.account_notifications(user_id)
  where kind = 'account_requested' and status in ('pending', 'sending');

create or replace function public.enqueue_new_account_notification()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.account_notifications(user_id, kind)
  values (new.user_id, 'account_requested')
  on conflict do nothing;
  return new;
end;
$$;
revoke execute on function public.enqueue_new_account_notification() from public, anon, authenticated;

create function public.request_account_access_again(p_user_id uuid)
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
  select profile.status into old_status
  from public.account_profiles as profile
  where profile.user_id = p_user_id
  for update;

  if not found then
    return;
  end if;

  -- Only a blocked account changes; trial_links_used is preserved.
  if old_status = 'rejected' then
    update public.account_profiles as profile
    set status = 'pending', updated_at = now()
    where profile.user_id = p_user_id;

    -- The profile row lock serializes requests; reuse any unfinished event instead of adding one.
    if not exists (
      select 1 from public.account_notifications as event
      where event.user_id = p_user_id
        and event.kind = 'account_requested'
        and event.status in ('pending', 'sending')
    ) then
      insert into public.account_notifications(user_id, kind)
      values (p_user_id, 'account_requested')
      returning id into notification_id;
    else
      select event.id into notification_id
      from public.account_notifications as event
      where event.user_id = p_user_id
        and event.kind = 'account_requested'
        and event.status = 'pending';
    end if;
  end if;

  return query
  select old_status, profile.user_id, profile.email, profile.status,
         profile.trial_links_used, profile.created_at, notification_id
  from public.account_profiles as profile
  where profile.user_id = p_user_id;
end;
$$;

revoke execute on function public.request_account_access_again(uuid)
  from public, anon, authenticated;
grant execute on function public.request_account_access_again(uuid) to service_role;
