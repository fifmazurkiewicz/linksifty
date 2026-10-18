-- Separate image-reading spend from assessment, using the same monthly ledger.
alter table public.usage_reservations add column purpose text not null default 'analysis'
  check (purpose in ('analysis','image_extraction'));
alter table public.jobs add column image_reservation_id uuid
  references public.usage_reservations(id) on delete set null;
drop index public.one_active_job_provider_reservation;
create unique index one_active_job_provider_reservation
  on public.usage_reservations(job_id,provider,purpose) where state='reserved';

create function public.reserve_image_reading(p_user_id uuid,p_job_id uuid,p_lease uuid,p_amount numeric)
returns table (id uuid) language plpgsql security definer set search_path=public as $$
declare j public.jobs; b numeric; s numeric; pending numeric; reservation uuid;
  m date := date_trunc('month',now() at time zone 'UTC')::date;
begin
  if p_amount is null or p_amount<=0 or p_amount>1000000 then
    raise exception 'invalid_reservation' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  perform public.get_user_settings(p_user_id);
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  select * into j from public.jobs where jobs.id=p_job_id and user_id=p_user_id
    and lease_token=p_lease and lease_expires_at>now() and status='processing' for update;
  if not found or not j.x_fetch_started or j.image_reservation_id is not null
    or not exists(select 1 from public.items where items.id=j.item_id and user_id=p_user_id and expires_at>now())
    then return; end if;
  select coalesce(sum(spent_usd),0) into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then
    update public.jobs set status='awaiting_manual_content',processing_stage='image_budget_exhausted',
      lease_token=null,lease_expires_at=null,updated_at=now() where jobs.id=j.id;
    update public.items set status='awaiting_manual_content',processing_stage='image_budget_exhausted',
      failure_reason='image_budget_exhausted',updated_at=now() where items.id=j.item_id and user_id=p_user_id;
    return;
  end if;
  insert into public.usage_reservations(user_id,job_id,month,amount_usd,provider,purpose)
    values(p_user_id,j.id,m,p_amount,'openrouter','image_extraction') returning usage_reservations.id into reservation;
  update public.jobs set image_reservation_id=reservation where jobs.id=j.id;
  return query select reservation;
end;
$$;

create function public.record_image_generation(p_user_id uuid,p_job_id uuid,p_reservation uuid,p_generation text)
returns setof public.usage_reservations language plpgsql security definer set search_path=public as $$
begin
  -- Accounting survives lease loss and content deletion; retain only the first ID.
  if p_generation is not null and length(p_generation) between 1 and 200 then
    return query update public.usage_reservations set generation_id=p_generation
      where user_id=p_user_id and id=p_reservation and purpose='image_extraction'
        and (job_id=p_job_id or job_id is null)
        and (generation_id is null or generation_id=p_generation) returning *;
  end if;
end;
$$;

-- Only explicit terminal-fetch Retry admits another X read and image batch.
create or replace function public.resume_processing_item(p_user_id uuid,p_item_id uuid)
returns setof public.items language plpgsql security definer set search_path=public as $$
declare j public.jobs; i public.items;
begin
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  select * into j from public.jobs where item_id=p_item_id and user_id=p_user_id
    and ((status='failed' and processing_stage in ('budget_exhausted','not_configured','invalid_model_output','provider_rejected'))
      or (status='awaiting_manual_content' and processing_stage not in ('x_attempt_uncertain','image_reading_uncertain'))) for update;
  if not found then return; end if;
  select * into i from public.items where items.id=p_item_id and user_id=p_user_id and status=j.status and expires_at>now() for update;
  if not found then return; end if;
  if j.status='awaiting_manual_content' and (i.original_url is null or i.failure_reason in ('x_attempt_uncertain','image_reading_uncertain')) then return; end if;
  if exists(select 1 from public.items other where other.user_id=p_user_id and other.id<>i.id
    and public.canonical_analysis_url(other.original_url)=public.canonical_analysis_url(i.original_url)
    and other.expires_at>now() and other.status in ('queued','processing','completed')) then raise exception 'duplicate_link'; end if;
  if exists(select 1 from public.usage_reservations where (job_id=j.id or id=j.reservation_id) and state='reserved') then return; end if;
  update public.jobs set status='queued',processing_stage='queued',reservation_id=null,model_result=null,
    threshold_snapshot=null,rubric_snapshot=null,lease_token=null,lease_expires_at=null,
    image_reservation_id=case when j.status='awaiting_manual_content' then null else image_reservation_id end,
    x_fetch_started=case when j.status='awaiting_manual_content' then false else x_fetch_started end,
    updated_at=now() where jobs.id=j.id;
  return query update public.items set status='queued',processing_stage='queued',failure_reason=null,updated_at=now()
    where items.id=p_item_id and user_id=p_user_id returning *;
end;
$$;

revoke execute on function public.reserve_image_reading(uuid,uuid,uuid,numeric) from public,anon,authenticated;
revoke execute on function public.record_image_generation(uuid,uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.reserve_image_reading(uuid,uuid,uuid,numeric) to service_role;
grant execute on function public.record_image_generation(uuid,uuid,uuid,text) to service_role;
revoke execute on function public.resume_processing_item(uuid,uuid) from public,anon,authenticated;
grant execute on function public.resume_processing_item(uuid,uuid) to service_role;
notify pgrst,'reload schema';
