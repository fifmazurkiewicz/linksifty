-- Topic-relevant source selection is a separate, one-shot OpenRouter operation.
alter table public.usage_reservations drop constraint usage_reservations_purpose_check;
alter table public.usage_reservations add constraint usage_reservations_purpose_check
  check (purpose in ('analysis','image_extraction','source_selection'));
alter table public.jobs add column selection_reservation_id uuid
  references public.usage_reservations(id) on delete set null;

-- Existing opt-ins predate the Jev charge/data disclosure. With workers paused,
-- leave saved research intact and disable new discovery on older unfinished jobs.
update public.jobs set web_search=false where web_search and search_context is null;

create function public.reserve_source_selection(p_user_id uuid,p_job_id uuid,p_lease uuid,p_amount numeric)
returns table (id uuid) language plpgsql security definer set search_path=public as $$
declare j public.jobs; b numeric; s numeric; pending numeric; reservation uuid;
  m date := date_trunc('month',now() at time zone 'UTC')::date;
begin
  if p_amount is null or p_amount<=0 or p_amount>0.02688 then
    raise exception 'invalid_reservation' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  perform public.get_user_settings(p_user_id);
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  select * into j from public.jobs where jobs.id=p_job_id and user_id=p_user_id
    and lease_token=p_lease and lease_expires_at>now() and status='processing' for update;
  if not found or not j.web_search or j.selection_reservation_id is not null
    or not exists(select 1 from public.items where items.id=j.item_id and user_id=p_user_id and expires_at>now())
    or not exists(select 1 from public.source_contents where item_id=j.item_id and user_id=p_user_id)
    or not exists(select 1 from public.usage_reservations where usage_reservations.id=j.search_reservation_id
      and user_id=p_user_id and provider='brave' and state='settled') then return; end if;
  select coalesce(sum(spent_usd),0) into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then return; end if;
  insert into public.usage_reservations(user_id,job_id,month,amount_usd,provider,purpose)
    values(p_user_id,j.id,m,p_amount,'openrouter','source_selection') returning usage_reservations.id into reservation;
  update public.jobs set selection_reservation_id=reservation where jobs.id=j.id;
  return query select reservation;
end;
$$;

create function public.record_source_selection_generation(p_user_id uuid,p_job_id uuid,p_reservation uuid,p_generation text)
returns setof public.usage_reservations language plpgsql security definer set search_path=public as $$
begin
  if p_generation is not null and length(p_generation) between 1 and 200 then
    return query update public.usage_reservations set generation_id=p_generation
      where user_id=p_user_id and id=p_reservation and purpose='source_selection'
        and (job_id=p_job_id or job_id is null)
        and (generation_id is null or generation_id=p_generation) returning *;
  end if;
end;
$$;

-- A reclaimed worker must see the prior selection admission and never resend it.
drop function public.claim_processing_job(uuid);
create function public.claim_processing_job(p_user_id uuid)
returns table (id uuid, item_id uuid, user_id uuid, lease_token uuid, original_url text, source_text text,
 threshold_snapshot numeric, reservation_id uuid, generation_id text, actual_usd numeric, reservation_state text, model_result jsonb, web_search boolean, search_reservation_id uuid, search_context jsonb, rubric_snapshot jsonb, selection_reservation_id uuid)
language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  if not exists (select 1 from public.account_profiles where account_profiles.user_id = p_user_id and status <> 'rejected') then return; end if;
  update public.jobs set status = 'processing', attempts = attempts + 1, lease_token = gen_random_uuid(), lease_expires_at = now() + interval '60 seconds', heartbeat_at = now()
   where jobs.id = (select q.id from public.jobs q join public.items i on i.id = q.item_id and i.user_id = q.user_id
    where q.user_id = p_user_id and i.expires_at > now() and (q.status = 'queued' or (q.status = 'processing' and q.lease_expires_at < now())
      or (q.status = 'failed' and q.processing_stage = 'cost_unknown' and q.updated_at < now() - interval '30 seconds'
          and exists (select 1 from public.usage_reservations r where r.id = q.reservation_id
            and (r.generation_id is not null or r.state = 'settled'))))
    order by q.created_at for update of q skip locked limit 1) returning * into j;
  if not found then return; end if;
  return query select j.id, j.item_id, j.user_id, j.lease_token, i.original_url, c.content,
    j.threshold_snapshot, j.reservation_id, u.generation_id, u.actual_usd, u.state, j.model_result, j.web_search, j.search_reservation_id, j.search_context, j.rubric_snapshot, j.selection_reservation_id
    from public.items i left join public.source_contents c on c.item_id = i.id and c.user_id = p_user_id
    left join public.usage_reservations u on u.id = j.reservation_id and u.user_id = p_user_id
    where i.id = j.item_id and i.user_id = p_user_id;
end;
$$;

revoke execute on function public.reserve_source_selection(uuid,uuid,uuid,numeric) from public,anon,authenticated;
revoke execute on function public.record_source_selection_generation(uuid,uuid,uuid,text) from public,anon,authenticated;
revoke execute on function public.claim_processing_job(uuid) from public,anon,authenticated;
grant execute on function public.reserve_source_selection(uuid,uuid,uuid,numeric) to service_role;
grant execute on function public.record_source_selection_generation(uuid,uuid,uuid,text) to service_role;
grant execute on function public.claim_processing_job(uuid) to service_role;
notify pgrst,'reload schema';
