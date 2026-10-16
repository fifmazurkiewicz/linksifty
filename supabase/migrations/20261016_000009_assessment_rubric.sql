-- Per-account rubric editing and immutable model/scoring snapshots.
create function public.default_assessment_rubric() returns jsonb
language sql immutable set search_path=public as $rubric$
select '{"criteria": [{"name": "novelty", "description": "Does the material offer new information or a useful new perspective?", "weight": 1}, {"name": "evidence", "description": "Are its claims supported by concrete data, examples and cited evidence?", "weight": 2}, {"name": "practicality", "description": "Can the reader apply the information to a real task or decision?", "weight": 1}, {"name": "source_credibility", "description": "Is the author or publisher qualified, transparent and trustworthy?", "weight": 2}, {"name": "replicability", "description": "Are there enough methods and details to reproduce the actions or results?", "weight": 2}, {"name": "independent_corroboration", "description": "Do independent supplied sources corroborate the claims?", "weight": 1}, {"name": "absence_of_conflict_of_interest", "description": "Are interests disclosed and promotional incentives unlikely to distort the claims?", "weight": 2}, {"name": "concreteness", "description": "Does the material provide specific details rather than slogans or superlatives?", "weight": 1}]}'::jsonb;
$rubric$;

create function public.valid_assessment_rubric(p_rubric jsonb) returns boolean
language plpgsql immutable set search_path=public as $$
declare e jsonb; seen text[] := '{}'; allowed text[] := array[
 'novelty','evidence','practicality','source_credibility','replicability',
 'independent_corroboration','absence_of_conflict_of_interest','concreteness'];
begin
 if p_rubric is null or jsonb_typeof(p_rubric) <> 'object' then return false; end if;
 if p_rubric - 'criteria' <> '{}'::jsonb or jsonb_typeof(p_rubric->'criteria') is distinct from 'array' then return false; end if;
 if jsonb_array_length(p_rubric->'criteria') <> 8 then return false; end if;
 for e in select * from jsonb_array_elements(p_rubric->'criteria') loop
  if jsonb_typeof(e) <> 'object' then return false; end if;
  if e - array['name','description','weight'] <> '{}'::jsonb
   or jsonb_typeof(e->'name') is distinct from 'string'
   or jsonb_typeof(e->'description') is distinct from 'string'
   or jsonb_typeof(e->'weight') is distinct from 'number' then return false; end if;
  if not (e->>'name' = any(allowed)) or e->>'name' = any(seen)
   or e->>'weight' !~ '^(10|[1-9])$'
   or length(e->>'description') not between 1 and 1000
   or length(btrim(e->>'description', chr(9) || chr(10) || chr(11) || chr(12) || chr(13) || chr(28) || chr(29) || chr(30) || chr(31) || chr(32) || chr(133) || chr(160) || chr(5760) || chr(8192) || chr(8193) || chr(8194) || chr(8195) || chr(8196) || chr(8197) || chr(8198) || chr(8199) || chr(8200) || chr(8201) || chr(8202) || chr(8232) || chr(8233) || chr(8239) || chr(8287) || chr(12288)))=0 then return false; end if;
  seen := array_append(seen,e->>'name');
 end loop;
 return true;
end;
$$;

alter table public.settings add column rubric jsonb not null default public.default_assessment_rubric()
 check (public.valid_assessment_rubric(rubric));
alter table public.jobs add column rubric_snapshot jsonb check (rubric_snapshot is null or public.valid_assessment_rubric(rubric_snapshot));
alter table public.usage_reservations add column rubric_snapshot jsonb not null default public.default_assessment_rubric()
 check (public.valid_assessment_rubric(rubric_snapshot));
alter table public.assessments add column rubric_snapshot jsonb not null default public.default_assessment_rubric()
 check (public.valid_assessment_rubric(rubric_snapshot));
update public.jobs set rubric_snapshot=public.default_assessment_rubric() where reservation_id is not null or model_result is not null;

create function public.update_user_assessment_settings(p_user_id uuid,p_threshold numeric,p_rubric jsonb default null)
returns setof public.settings language plpgsql security definer set search_path=public as $$
begin
 if p_threshold is null or p_threshold::text in ('NaN','Infinity','-Infinity') or p_threshold<40 or p_threshold>100 then raise exception 'invalid_threshold'; end if;
 if p_rubric is not null and not public.valid_assessment_rubric(p_rubric) then raise exception 'invalid_rubric'; end if;
 perform public.get_user_settings(p_user_id);
 return query update public.settings set valuable_threshold=p_threshold,rubric=coalesce(p_rubric,rubric),updated_at=now()
  where user_id=p_user_id returning *;
end;
$$;

create or replace function public.reserve_analysis(p_user_id uuid, p_job_id uuid, p_lease uuid, p_amount numeric)
returns setof public.usage_reservations language plpgsql security definer set search_path = public as $$
declare j public.jobs; u public.usage_reservations; m date := date_trunc('month', now() at time zone 'UTC')::date;
 s numeric; r numeric; b numeric;
begin
  if p_amount is null or p_amount <= 0 or p_amount > 1000000 then raise exception 'invalid_reservation'; end if;
  perform public.get_user_settings(p_user_id);
  select monthly_budget_usd into b from public.settings where user_id = p_user_id for update;
  select * into j from public.jobs where id = p_job_id and user_id = p_user_id and lease_token = p_lease
    and lease_expires_at > now() and status = 'processing' for update;
  if not found then return; end if;
  if not exists (select 1 from public.account_profiles where user_id = p_user_id and status <> 'rejected') then return; end if;
  if j.reservation_id is not null then
    return query select * from public.usage_reservations where id = j.reservation_id and user_id = p_user_id;
    return;
  end if;
  insert into public.usage_months(user_id, month) values (p_user_id, m) on conflict do nothing;
  select spent_usd into s from public.usage_months where user_id = p_user_id and month = m;
  select coalesce(sum(amount_usd), 0) into r from public.usage_reservations where user_id = p_user_id and state = 'reserved';
  if s + r + p_amount > b then
    update public.jobs set status = 'failed', processing_stage = 'budget_exhausted', error_code = 'budget_exhausted', lease_token = null, lease_expires_at = null where id = j.id;
    update public.items set status = 'failed', processing_stage = 'budget_exhausted', failure_reason = 'budget_exhausted', updated_at = now() where id = j.item_id and user_id = p_user_id;
    return;
  end if;
  insert into public.usage_reservations(user_id, job_id, month, amount_usd, threshold_snapshot, rubric_snapshot)
    values (p_user_id, j.id, m, p_amount, coalesce(j.threshold_snapshot,
    (select valuable_threshold from public.settings where user_id = p_user_id)),
    coalesce(j.rubric_snapshot,(select rubric from public.settings where user_id=p_user_id))) returning * into u;
  update public.jobs set reservation_id = u.id, threshold_snapshot = u.threshold_snapshot, rubric_snapshot=u.rubric_snapshot where id = j.id;
  return next u;
end;
$$;

drop function public.claim_processing_job(uuid);
create function public.claim_processing_job(p_user_id uuid)
returns table (id uuid, item_id uuid, user_id uuid, lease_token uuid, original_url text, source_text text,
 threshold_snapshot numeric, reservation_id uuid, generation_id text, actual_usd numeric, reservation_state text, model_result jsonb, web_search boolean, search_reservation_id uuid, search_context jsonb, rubric_snapshot jsonb)
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
    j.threshold_snapshot, j.reservation_id, u.generation_id, u.actual_usd, u.state, j.model_result, j.web_search, j.search_reservation_id, j.search_context, j.rubric_snapshot
    from public.items i left join public.source_contents c on c.item_id = i.id and c.user_id = p_user_id
    left join public.usage_reservations u on u.id = j.reservation_id and u.user_id = p_user_id
    where i.id = j.item_id and i.user_id = p_user_id;
end;
$$;

create or replace function public.complete_processing_job(p_user_id uuid, p_job_id uuid, p_lease uuid, p_assessment jsonb, p_citations jsonb)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare j public.jobs; a uuid; c jsonb; source_text text; source_link text;
begin
  select * into j from public.jobs where id = p_job_id and user_id = p_user_id and lease_token = p_lease and lease_expires_at > now() for update;
  if not found then return; end if;
  if not exists (select 1 from public.source_contents where item_id = j.item_id and user_id = p_user_id)
    or not exists (select 1 from public.usage_reservations where id = j.reservation_id and user_id = p_user_id and state = 'settled') then return; end if;
  insert into public.assessments(item_id, user_id, note, criteria, score, verdict, threshold_snapshot, rubric_snapshot)
    values (j.item_id, p_user_id, p_assessment->>'note', p_assessment->'criteria', (p_assessment->>'score')::numeric,
    (p_assessment->>'verdict')::public.verdict, j.threshold_snapshot,coalesce(j.rubric_snapshot,public.default_assessment_rubric())) returning id into a;
  for c in select * from jsonb_array_elements(p_citations) loop
    if coalesce(c->>'source_id', 'primary') = 'primary' then
      select sc.content, i.original_url into source_text, source_link from public.source_contents sc
        join public.items i on i.id=sc.item_id where sc.item_id=j.item_id and sc.user_id=p_user_id;
    else
      select s->>'text', s->>'url' into source_text, source_link
        from jsonb_array_elements(j.search_context->'sources') s where s->>'id'=c->>'source_id';
    end if;
    if source_text is null or (c->>'start_position')::int < 0 or (c->>'end_position')::int <= (c->>'start_position')::int
      or substring(source_text from (c->>'start_position')::int+1 for (c->>'end_position')::int-(c->>'start_position')::int) <> c->>'excerpt'
      then raise exception 'invalid_citation'; end if;
    insert into public.citations(id, assessment_id, user_id, excerpt, start_position, end_position, source_url, source_id)
      values ((c->>'id')::uuid, a, p_user_id, c->>'excerpt', (c->>'start_position')::int, (c->>'end_position')::int, source_link, coalesce(c->>'source_id','primary'));
  end loop;
  update public.jobs set status = 'completed', processing_stage = 'completed', model_result = null, lease_token = null, lease_expires_at = null, updated_at = now() where id = j.id;
  return query update public.items set status = 'completed', processing_stage = 'completed', failure_reason = null, updated_at = now()
    where items.id = j.item_id and items.user_id = p_user_id returning *;
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
    threshold_snapshot = null, rubric_snapshot=null, lease_token = null, lease_expires_at = null where id = j.id;
  return query update public.items set status = 'queued', processing_stage = 'queued', failure_reason = null, updated_at = now()
    where id = p_item_id and user_id = p_user_id and expires_at > now() returning *;
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
    if exists(select 1 from public.jobs j join public.usage_reservations r on r.id=j.reservation_id where j.item_id=i.id and j.user_id=p_user_id and r.state='reserved') then return; end if;
    update public.jobs set status = 'queued', processing_stage = 'queued', model_result = null, reservation_id = null,
      threshold_snapshot=null, rubric_snapshot=null, lease_token = null, lease_expires_at = null where item_id = i.id and user_id = p_user_id;
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

do $$
declare f record;
begin
 for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('default_assessment_rubric','valid_assessment_rubric','update_user_assessment_settings','reserve_analysis','claim_processing_job','complete_processing_job','resume_processing_item','paste_item_content') loop
  execute format('revoke execute on function %s from public, anon, authenticated',f.signature);
  execute format('grant execute on function %s to service_role',f.signature);
 end loop;
end;
$$;
notify pgrst,'reload schema';
