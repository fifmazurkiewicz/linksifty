-- One confirmed transaction for single/bulk deletion; paid accounting survives.
create function public.delete_items(p_user_id uuid, p_item_ids uuid[], p_confirmed boolean)
returns table (id uuid)
language plpgsql security definer set search_path=public as $$
begin
  if p_confirmed is distinct from true then
    raise exception 'deletion_confirmation_required' using errcode='22023';
  end if;
  if p_item_ids is null or cardinality(p_item_ids) not between 1 and 50
    or array_position(p_item_ids,null) is not null
    or cardinality(p_item_ids) <> (select count(distinct value) from unnest(p_item_ids) value)
    then raise exception 'invalid_deletion_selection' using errcode='22023'; end if;

  -- Serialize paste/resume and budget writes. Late results lock reservations
  -- before jobs; completion locks jobs before items. Follow those orders.
  perform 1 from public.account_profiles where user_id=p_user_id for update;
  perform 1 from public.settings where user_id=p_user_id for update;
  perform 1 from public.usage_reservations r where r.user_id=p_user_id and r.job_id in (
    select j.id from public.jobs j where j.user_id=p_user_id and j.item_id=any(p_item_ids))
    order by r.id for update;
  perform 1 from public.jobs j where j.user_id=p_user_id and j.item_id=any(p_item_ids)
    order by j.id for update;
  perform 1 from public.items i where i.user_id=p_user_id and i.id=any(p_item_ids)
    order by i.id for update;
  if (select count(*) from public.items i where i.user_id=p_user_id and i.id=any(p_item_ids))
    <> cardinality(p_item_ids) then return; end if;

  -- Historical schemas do not enforce composite owner foreign keys. Fail
  -- closed rather than cascading into any inconsistently owned child row.
  if exists(select 1 from public.source_contents where item_id=any(p_item_ids) and user_id<>p_user_id)
    or exists(select 1 from public.jobs where item_id=any(p_item_ids) and user_id<>p_user_id)
    or exists(select 1 from public.assessments where item_id=any(p_item_ids) and user_id<>p_user_id)
    or exists(select 1 from public.chat_messages where item_id=any(p_item_ids) and user_id<>p_user_id)
    or exists(select 1 from public.citations c join public.assessments a on a.id=c.assessment_id
      where a.item_id=any(p_item_ids) and c.user_id<>p_user_id)
    or exists(select 1 from public.usage_reservations r join public.jobs j on j.id=r.job_id
      where j.item_id=any(p_item_ids) and r.user_id<>p_user_id)
    then return; end if;

  -- No article text is in the ledger. Remove custom rubric text as well.
  -- ON DELETE SET NULL detaches retained reservations from the removed jobs.
  update public.usage_reservations r set rubric_snapshot=public.legacy_assessment_rubric()
    where r.user_id=p_user_id and r.job_id in (
      select j.id from public.jobs j where j.user_id=p_user_id and j.item_id=any(p_item_ids));
  return query delete from public.items i where i.user_id=p_user_id and i.id=any(p_item_ids)
    returning i.id;
end;
$$;

revoke execute on function public.delete_items(uuid,uuid[],boolean) from public,anon,authenticated;
grant execute on function public.delete_items(uuid,uuid[],boolean) to service_role;
notify pgrst, 'reload schema';
