-- A partial preview is metadata, never complete source text or an assessment.
alter table public.items add column partial_overview text
  check (partial_overview is null or (length(btrim(partial_overview)) between 1 and 400
    and partial_overview !~ '[[:cntrl:]]'));
alter table public.jobs add column partial_preview_allowed boolean not null default false;
alter table public.jobs add column preview_reservation_id uuid
  references public.usage_reservations(id) on delete set null;
alter table public.usage_reservations drop constraint usage_reservations_purpose_check;
alter table public.usage_reservations add constraint usage_reservations_purpose_check
  check (purpose in ('analysis','image_extraction','source_selection','title','partial_preview'));

create function public.allow_partial_previews(p_user_id uuid,p_item_ids uuid[],p_confirmed boolean)
returns setof public.jobs language plpgsql security definer set search_path=public as $$
begin
  if p_confirmed is distinct from true then raise exception 'preview_consent_required'; end if;
  if p_item_ids is null or cardinality(p_item_ids) not between 1 and 5 then return; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  return query update public.jobs q set partial_preview_allowed=true
    from public.items i where q.item_id=i.id and q.user_id=p_user_id and i.user_id=p_user_id
      and q.item_id=any(p_item_ids) and q.status in ('queued','processing')
      and i.expires_at>now() and i.original_url is not null returning q.*;
end;
$$;

create function public.reserve_partial_preview(p_user_id uuid,p_job_id uuid,p_lease uuid,p_amount numeric)
returns table(id uuid) language plpgsql security definer set search_path=public as $$
declare j public.jobs; b numeric; s numeric; pending numeric; reservation uuid;
  m date:=date_trunc('month',now() at time zone 'UTC')::date;
begin
  if p_amount is null or p_amount<=0 or p_amount>0.14848 then
    raise exception 'invalid_reservation' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  perform public.get_user_settings(p_user_id);
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  select * into j from public.jobs where jobs.id=p_job_id and user_id=p_user_id
    and lease_token=p_lease and lease_expires_at>now() and status='processing' for update;
  if not found or not j.partial_preview_allowed or j.preview_reservation_id is not null
    or not exists(select 1 from public.items where items.id=j.item_id and user_id=p_user_id
      and status='processing' and expires_at>now() and partial_overview is null)
    or exists(select 1 from public.source_contents where item_id=j.item_id and user_id=p_user_id)
    then return; end if;
  select coalesce(sum(spent_usd),0) into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then return; end if;
  insert into public.usage_reservations(user_id,job_id,month,amount_usd,provider,purpose)
    values(p_user_id,j.id,m,p_amount,'openrouter','partial_preview') returning usage_reservations.id into reservation;
  update public.jobs set preview_reservation_id=reservation where jobs.id=j.id;
  return query select reservation;
end;
$$;

create function public.record_partial_preview(
  p_user_id uuid,p_job_id uuid,p_lease uuid,p_reservation uuid,p_overview text,p_generation text
) returns setof public.items language plpgsql security definer set search_path=public as $$
declare j public.jobs;
begin
  perform 1 from public.account_profiles where user_id=p_user_id for update;
  -- Keep billing metadata even after deletion, rejection or lease loss.
  if p_generation is not null and length(p_generation) between 1 and 200 then
    update public.usage_reservations set generation_id=p_generation
      where user_id=p_user_id and id=p_reservation and purpose='partial_preview'
        and (job_id=p_job_id or job_id is null)
        and (generation_id is null or generation_id=p_generation);
  end if;
  if p_overview is null or length(btrim(p_overview)) not between 1 and 400
    or p_overview ~ '[[:cntrl:]]' then return; end if;
  if not exists(select 1 from public.account_profiles where user_id=p_user_id and status<>'rejected') then return; end if;
  select * into j from public.jobs where jobs.id=p_job_id and user_id=p_user_id
    and lease_token=p_lease and lease_expires_at>now() and status='processing'
    and partial_preview_allowed and preview_reservation_id=p_reservation for update;
  if not found or not exists(select 1 from public.usage_reservations where id=p_reservation
    and user_id=p_user_id and job_id=p_job_id and purpose='partial_preview') then return; end if;
  return query update public.items set partial_overview=btrim(p_overview),updated_at=now()
    where items.id=j.item_id and user_id=p_user_id and expires_at>now()
      and status='processing' and partial_overview is null returning *;
end;
$$;

-- Three-argument RPC overloads atomically save consent before a job is visible.
-- Older clients keep the original two-argument behavior, with consent off.
create function public.submit_fetch_items(p_user_id uuid,p_urls text[],p_allow_partial_preview boolean)
returns setof public.items language plpgsql security definer set search_path=public as $$
declare i public.items;
begin
  for i in select * from public.submit_fetch_items(p_user_id,p_urls) loop
    if p_allow_partial_preview is true then
      perform public.allow_partial_previews(p_user_id,array[i.id],true);
    end if;
    return next i;
  end loop;
end;
$$;
create function public.submit_search_items(p_user_id uuid,p_urls text[],p_allow_partial_preview boolean)
returns setof public.items language plpgsql security definer set search_path=public as $$
declare i public.items;
begin
  for i in select * from public.submit_search_items(p_user_id,p_urls) loop
    if p_allow_partial_preview is true then
      perform public.allow_partial_previews(p_user_id,array[i.id],true);
    end if;
    return next i;
  end loop;
end;
$$;
create function public.resume_processing_item(p_user_id uuid,p_item_id uuid,p_allow_partial_preview boolean)
returns setof public.items language plpgsql security definer set search_path=public as $$
declare i public.items;
begin
  for i in select * from public.resume_processing_item(p_user_id,p_item_id) loop
    if p_allow_partial_preview is true then
      perform public.allow_partial_previews(p_user_id,array[i.id],true);
    end if;
    return next i;
  end loop;
end;
$$;

drop function public.list_processing_items(uuid);
create function public.list_processing_items(p_user_id uuid)
returns table(id uuid,user_id uuid,original_url text,title text,status public.item_status,unread boolean,
 processing_stage text,failure_reason text,updated_at timestamptz,score numeric,verdict public.verdict,
 worker_active boolean,partial_overview text,preview_charge_pending boolean)
language sql security definer set search_path=public as $$
 select i.id,i.user_id,i.original_url,i.title,i.status,i.unread,i.processing_stage,
  case when i.processing_stage='invalid_model_output' then coalesce(j.model_result->>'failure_reason',i.failure_reason) else i.failure_reason end,
  i.updated_at,a.score,a.verdict,
  coalesce(j.status='processing' and j.heartbeat_at>now()-interval '45 seconds' and j.lease_expires_at>now(),false),
  i.partial_overview,coalesce(u.state='reserved',false)
 from public.items i left join public.assessments a on a.item_id=i.id and a.user_id=p_user_id
 left join public.jobs j on j.item_id=i.id and j.user_id=p_user_id
 left join public.usage_reservations u on u.id=j.preview_reservation_id and u.user_id=p_user_id
 where i.user_id=p_user_id and i.expires_at>now()
 order by i.unread desc,a.score desc nulls last,i.created_at desc limit 50;
$$;

do $$
declare f record;
begin
  for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname in ('allow_partial_previews','reserve_partial_preview','record_partial_preview','list_processing_items','submit_fetch_items','submit_search_items','resume_processing_item') loop
    execute format('revoke execute on function %s from public,anon,authenticated',f.signature);
    execute format('grant execute on function %s to service_role',f.signature);
  end loop;
end;
$$;
notify pgrst,'reload schema';
