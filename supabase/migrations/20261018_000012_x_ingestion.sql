-- A durable, owner/lease-fenced attempt marker prevents crash recovery from
-- repeating potentially billed X reads. Cached source text remains reusable.
alter table public.jobs add column x_fetch_started boolean not null default false;

create function public.begin_x_fetch(p_user_id uuid, p_job_id uuid, p_lease uuid)
returns table (admitted boolean)
language plpgsql security definer set search_path = public as $$
declare affected integer;
begin
  update public.jobs j set x_fetch_started = true
    where j.id = p_job_id and j.user_id = p_user_id
      and j.lease_token = p_lease and j.status = 'processing'
      and j.lease_expires_at > now() and not j.x_fetch_started
      and exists (select 1 from public.items i where i.id = j.item_id
        and i.user_id = p_user_id and i.expires_at > now())
      and exists (select 1 from public.account_profiles a where a.user_id = p_user_id
        and a.status <> 'rejected');
  get diagnostics affected = row_count;
  return query select affected = 1;
end;
$$;
revoke all on function public.begin_x_fetch(uuid,uuid,uuid) from public, anon, authenticated;
grant execute on function public.begin_x_fetch(uuid,uuid,uuid) to service_role;
