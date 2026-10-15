-- Preserve legacy duplicates; reject new duplicates atomically under the owner lock.
create function public.canonical_analysis_url(p_url text)
returns text language plpgsql immutable strict set search_path=pg_catalog as $$
declare parts text[]; authority text; suffix text;
begin
  parts := regexp_match(trim(p_url), '^(https?)://([^/?#]+)([^#]*)', 'i');
  if parts is null then return null; end if;
  authority := lower(parts[2]);
  if lower(parts[1])='https' then authority:=regexp_replace(authority, ':443$', '');
  else authority:=regexp_replace(authority, ':80$', ''); end if;
  suffix:=parts[3];
  if suffix='' then suffix:='/'; elsif left(suffix,1)='?' then suffix:='/'||suffix; end if;
  return lower(parts[1])||'://'||authority||suffix;
end;
$$;
create or replace function public.submit_fetch_items(p_user_id uuid, p_urls text[])
returns setof public.items
language plpgsql
security definer
set search_path = public
as $$
declare
  submitted public.items;
  source_url text;
  current_status public.account_status;
  used_trials integer;
  requested_links integer;
begin
  requested_links := cardinality(p_urls);
  if p_user_id is null or requested_links is null or requested_links not between 1 and 5 then
    raise exception 'A user and one to five URLs are required';
  end if;

  select status, trial_links_used
  into current_status, used_trials
  from public.account_profiles
  where user_id = p_user_id
  for update;

  if not found then
    raise exception using errcode = 'P0001', message = 'account_profile_missing';
  end if;
  if current_status = 'rejected' then
    raise exception using errcode = 'P0001', message = 'account_rejected';
  end if;
  foreach source_url in array p_urls loop
    if public.canonical_analysis_url(source_url) is null then
      raise exception 'Only HTTP and HTTPS URLs are accepted';
    end if;
  end loop;
  if (select count(distinct public.canonical_analysis_url(u)) from unnest(p_urls) u) <> requested_links
    or exists(select 1 from public.items i where i.user_id=p_user_id and i.expires_at>now()
      and public.canonical_analysis_url(i.original_url) in (select public.canonical_analysis_url(u) from unnest(p_urls) u))
    then raise exception 'duplicate_link'; end if;
  if current_status = 'pending' and used_trials + requested_links > 3 then
    raise exception using errcode = 'P0001', message = 'account_trial_limit_exceeded';
  end if;

  foreach source_url in array p_urls loop
    if source_url is null or source_url !~ '^https?://' then
      raise exception 'Only HTTP and HTTPS URLs are accepted';
    end if;
    insert into public.items(user_id, original_url, canonical_url, input_mode, title)
      values(p_user_id, source_url, public.canonical_analysis_url(source_url), 'fetch', source_url) returning * into submitted;
    insert into public.jobs(user_id, item_id) values(p_user_id, submitted.id);
    return next submitted;
  end loop;

  if current_status = 'pending' then
    update public.account_profiles
    set trial_links_used = used_trials + requested_links, updated_at = now()
    where user_id = p_user_id;
  end if;
end;
$$;

create or replace function public.resume_processing_item(p_user_id uuid, p_item_id uuid)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  perform 1 from public.account_profiles where user_id=p_user_id for update;
  select * into j from public.jobs where item_id = p_item_id and user_id = p_user_id and status = 'failed'
    and processing_stage in ('budget_exhausted', 'not_configured', 'invalid_model_output', 'provider_rejected') for update;
  if not found then return; end if;
  if exists(select 1 from public.items current_item join public.items other
      on other.user_id=current_item.user_id and other.id<>current_item.id
      and public.canonical_analysis_url(other.original_url)=public.canonical_analysis_url(current_item.original_url)
      where current_item.id=p_item_id and current_item.user_id=p_user_id
      and other.expires_at>now() and other.status in ('queued','processing','completed'))
    then raise exception 'duplicate_link'; end if;
  if exists (select 1 from public.usage_reservations where id = j.reservation_id and state = 'reserved') then return; end if;
  update public.jobs set status = 'queued', processing_stage = 'queued', reservation_id = null, model_result = null,
    threshold_snapshot = null, lease_token = null, lease_expires_at = null where id = j.id;
  return query update public.items set status = 'queued', processing_stage = 'queued', failure_reason = null, updated_at = now()
    where id = p_item_id and user_id = p_user_id and expires_at > now() returning *;
end;
$$;

revoke execute on function public.canonical_analysis_url(text) from public,anon,authenticated;
grant execute on function public.canonical_analysis_url(text) to service_role;
revoke execute on function public.submit_fetch_items(uuid,text[]) from public,anon,authenticated;
grant execute on function public.submit_fetch_items(uuid,text[]) to service_role;
revoke execute on function public.resume_processing_item(uuid,uuid) from public,anon,authenticated;
grant execute on function public.resume_processing_item(uuid,uuid) to service_role;
notify pgrst, 'reload schema';
