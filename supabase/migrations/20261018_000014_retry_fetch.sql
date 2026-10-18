-- Explicit queue Retry reuses the existing job, owner scope and budget guards.
create or replace function public.resume_processing_item(p_user_id uuid, p_item_id uuid)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare j public.jobs; i public.items;
begin
  perform 1 from public.account_profiles where user_id=p_user_id and status <> 'rejected' for update;
  if not found then return; end if;
  select * into j from public.jobs where item_id=p_item_id and user_id=p_user_id
    and ((status='failed' and processing_stage in ('budget_exhausted', 'not_configured', 'invalid_model_output', 'provider_rejected'))
      or (status='awaiting_manual_content' and processing_stage <> 'x_attempt_uncertain')) for update;
  if not found then return; end if;
  select * into i from public.items where id=p_item_id and user_id=p_user_id
    and status=j.status and expires_at>now() for update;
  if not found then return; end if;
  if j.status='awaiting_manual_content' and (i.original_url is null or i.failure_reason='x_attempt_uncertain') then return; end if;
  if exists(select 1 from public.items other where other.user_id=p_user_id and other.id<>i.id
      and public.canonical_analysis_url(other.original_url)=public.canonical_analysis_url(i.original_url)
      and other.expires_at>now() and other.status in ('queued','processing','completed'))
    then raise exception 'duplicate_link'; end if;
  if exists(select 1 from public.usage_reservations where (job_id=j.id or id=j.reservation_id) and state='reserved') then return; end if;
  update public.jobs set status='queued', processing_stage='queued', reservation_id=null, model_result=null,
    threshold_snapshot=null, rubric_snapshot=null, lease_token=null, lease_expires_at=null,
    x_fetch_started=case when j.status='awaiting_manual_content' then false else x_fetch_started end,
    updated_at=now() where id=j.id;
  return query update public.items set status='queued', processing_stage='queued', failure_reason=null, updated_at=now()
    where id=p_item_id and user_id=p_user_id returning *;
end;
$$;
revoke execute on function public.resume_processing_item(uuid,uuid) from public,anon,authenticated;
grant execute on function public.resume_processing_item(uuid,uuid) to service_role;
