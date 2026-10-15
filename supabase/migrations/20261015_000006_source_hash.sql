-- pgcrypto can be installed in extensions rather than public on Supabase.
-- Use PostgreSQL's built-in SHA256 so source writes do not depend on its schema.
-- Keep the fixed search_path and all existing ownership/lease guards.
create or replace function public.save_job_source(p_user_id uuid, p_job_id uuid, p_lease uuid, p_text text)
returns setof public.jobs language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  select * into j from public.jobs where id = p_job_id and user_id = p_user_id and lease_token = p_lease and lease_expires_at > now() for update;
  if not found then return; end if;
  if length(trim(p_text)) < 200 or octet_length(p_text) > 100000 then raise exception 'invalid_content'; end if;
  insert into public.source_contents(item_id, user_id, acquisition_method, content, content_hash)
    values (j.item_id, p_user_id, 'fetch', p_text, pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p_text, 'UTF8')), 'hex'))
    on conflict (item_id) do update set content = excluded.content, content_hash = excluded.content_hash
      where source_contents.user_id = p_user_id;
  if not found then raise exception 'source_owner_mismatch'; end if;
  return next j;
end;
$$;

create or replace function public.paste_item_content(p_user_id uuid, p_text text, p_item_id uuid default null)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare i public.items; p public.account_profiles;
begin
  if length(trim(p_text)) < 200 or octet_length(p_text) > 100000 then raise exception 'invalid_content'; end if;
  select * into p from public.account_profiles where user_id = p_user_id for update;
  if not found or p.status = 'rejected' then raise exception 'account_rejected'; end if;
  if p_item_id is null then
    if p.status = 'pending' and p.trial_links_used >= 3 then raise exception 'account_trial_limit_exceeded'; end if;
    insert into public.items(user_id, input_mode, title) values (p_user_id, 'paste', 'Pasted content') returning * into i;
    insert into public.jobs(item_id, user_id) values (i.id, p_user_id);
    if p.status = 'pending' then update public.account_profiles set trial_links_used = trial_links_used + 1 where user_id = p_user_id; end if;
  else
    select * into i from public.items where id = p_item_id and user_id = p_user_id and status = 'awaiting_manual_content' and expires_at > now() for update;
    if not found then return; end if;
    update public.jobs set status = 'queued', processing_stage = 'queued', model_result = null, reservation_id = null,
      lease_token = null, lease_expires_at = null where item_id = i.id and user_id = p_user_id;
    update public.items set status = 'queued', processing_stage = 'queued', failure_reason = null, updated_at = now() where id = i.id returning * into i;
  end if;
  insert into public.source_contents(item_id, user_id, acquisition_method, content, content_hash)
    values (i.id, p_user_id, 'paste', p_text, pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p_text, 'UTF8')), 'hex'))
    on conflict (item_id) do update set acquisition_method = 'paste', content = excluded.content, content_hash = excluded.content_hash
      where source_contents.user_id = p_user_id;
  if not found then raise exception 'source_owner_mismatch'; end if;
  return next i;
end;
$$;

revoke execute on function public.save_job_source(uuid, uuid, uuid, text) from public, anon, authenticated;
grant execute on function public.save_job_source(uuid, uuid, uuid, text) to service_role;
revoke execute on function public.paste_item_content(uuid, text, uuid) from public, anon, authenticated;
grant execute on function public.paste_item_content(uuid, text, uuid) to service_role;
