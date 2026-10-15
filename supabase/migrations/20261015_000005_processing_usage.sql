-- Server-only mutations; authenticated clients may read only their own content.
alter table public.settings add column monthly_budget_usd numeric(18,8) not null default 10
  check (monthly_budget_usd >= 0 and monthly_budget_usd <= 1000000);
update public.settings set monthly_budget_usd = monthly_budget_cents::numeric / 100;
alter table public.items add column processing_stage text not null default 'queued';
alter table public.jobs add column processing_stage text not null default 'queued';
alter table public.jobs add column threshold_snapshot numeric(5,2);
alter table public.jobs add column model_result jsonb;
alter table public.jobs add column heartbeat_at timestamptz;
alter table public.jobs drop constraint jobs_attempts_check;
alter table public.jobs add check (attempts >= 0);

create table public.usage_months (
  user_id uuid not null references auth.users(id) on delete cascade,
  month date not null, spent_usd numeric not null default 0 check (spent_usd >= 0),
  primary key (user_id, month)
);
create table public.usage_reservations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  job_id uuid references public.jobs(id) on delete set null,
  month date not null, amount_usd numeric not null check (amount_usd > 0),
  actual_usd numeric check (actual_usd >= 0),
  state text not null default 'reserved' check (state in ('reserved', 'settled')),
  generation_id text, threshold_snapshot numeric(5,2) not null default 60 check (threshold_snapshot between 40 and 100), created_at timestamptz not null default now()
);
create unique index one_active_job_reservation on public.usage_reservations(job_id) where state = 'reserved';
alter table public.jobs add column reservation_id uuid references public.usage_reservations(id) on delete set null;
alter table public.usage_months enable row level security;
alter table public.usage_reservations enable row level security;
create policy "usage owner read" on public.usage_months for select using (auth.uid() = user_id);
create policy "reservations owner read" on public.usage_reservations for select using (auth.uid() = user_id);
revoke all on public.usage_months, public.usage_reservations from anon, authenticated;
grant select on public.usage_months, public.usage_reservations to authenticated;
grant all on public.usage_months, public.usage_reservations to service_role;
revoke insert, update, delete, truncate, references, trigger on public.settings, public.items,
 public.jobs, public.source_contents, public.assessments, public.citations, public.chat_messages from anon, authenticated;

create function public.get_user_settings(p_user_id uuid)
returns setof public.settings language plpgsql security definer set search_path = public as $$
begin
  insert into public.settings(user_id) values (p_user_id) on conflict do nothing;
  return query select * from public.settings where user_id = p_user_id;
end;
$$;
create function public.update_user_threshold(p_user_id uuid, p_threshold numeric)
returns setof public.settings language plpgsql security definer set search_path = public as $$
begin
  if p_threshold is null or p_threshold < 40 or p_threshold > 100 then raise exception 'invalid_threshold'; end if;
  perform public.get_user_settings(p_user_id);
  return query update public.settings set valuable_threshold = p_threshold, updated_at = now()
    where user_id = p_user_id returning *;
end;
$$;
create function public.set_user_budget(p_user_id uuid, p_limit numeric)
returns setof public.settings language plpgsql security definer set search_path = public as $$
begin
  if p_limit is null or p_limit < 0 or p_limit > 1000000 then raise exception 'invalid_budget'; end if;
  if not exists (select 1 from public.account_profiles where user_id = p_user_id) then raise exception 'profile_missing'; end if;
  perform public.get_user_settings(p_user_id);
  return query update public.settings set monthly_budget_usd = p_limit, updated_at = now()
    where user_id = p_user_id returning *;
end;
$$;
create function public.get_usage_summary(p_user_id uuid)
returns table (month date, spent_usd numeric, reserved_usd numeric, limit_usd numeric, remaining_usd numeric, resets_at timestamptz)
language plpgsql security definer set search_path = public as $$
declare m date := date_trunc('month', now() at time zone 'UTC')::date; s numeric; r numeric; b numeric;
begin
  perform public.get_user_settings(p_user_id);
  -- One read snapshot avoids temporarily double-counting concurrent settlement.
  -- Unresolved prior-month calls still consume capacity until reconciled.
  select coalesce((select sum(u.spent_usd) from public.usage_months u where u.user_id = p_user_id and u.month = m), 0),
    coalesce((select sum(u.amount_usd) from public.usage_reservations u where u.user_id = p_user_id and u.state = 'reserved'), 0),
    cfg.monthly_budget_usd into s, r, b from public.settings cfg where cfg.user_id = p_user_id;
  return query select m, s, r, b, greatest(0, b - s - r), (m + interval '1 month') at time zone 'UTC';
end;
$$;

create function public.reserve_analysis(p_user_id uuid, p_job_id uuid, p_lease uuid, p_amount numeric)
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
  insert into public.usage_reservations(user_id, job_id, month, amount_usd, threshold_snapshot)
    values (p_user_id, j.id, m, p_amount, coalesce(j.threshold_snapshot,
    (select valuable_threshold from public.settings where user_id = p_user_id))) returning * into u;
  update public.jobs set reservation_id = u.id, threshold_snapshot = u.threshold_snapshot where id = j.id;
  return next u;
end;
$$;
create function public.settle_analysis(p_user_id uuid, p_reservation uuid, p_cost numeric)
returns setof public.usage_reservations language plpgsql security definer set search_path = public as $$
declare u public.usage_reservations;
begin
  if p_cost is null or p_cost < 0 or p_cost > 1000000 then raise exception 'invalid_cost'; end if;
  perform 1 from public.settings where user_id = p_user_id for update;
  select * into u from public.usage_reservations where id = p_reservation and user_id = p_user_id for update;
  if not found then return; end if;
  if u.state = 'reserved' then
    insert into public.usage_months(user_id, month, spent_usd) values (p_user_id, u.month, p_cost)
      on conflict (user_id, month) do update set spent_usd = public.usage_months.spent_usd + excluded.spent_usd;
    update public.usage_reservations set actual_usd = p_cost, state = 'settled' where id = u.id returning * into u;
  end if;
  return next u;
end;
$$;

create function public.claim_processing_job(p_user_id uuid)
returns table (id uuid, item_id uuid, user_id uuid, lease_token uuid, original_url text, source_text text,
 threshold_snapshot numeric, reservation_id uuid, generation_id text, actual_usd numeric, reservation_state text, model_result jsonb)
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
    j.threshold_snapshot, j.reservation_id, u.generation_id, u.actual_usd, u.state, j.model_result
    from public.items i left join public.source_contents c on c.item_id = i.id and c.user_id = p_user_id
    left join public.usage_reservations u on u.id = j.reservation_id and u.user_id = p_user_id
    where i.id = j.item_id and i.user_id = p_user_id;
end;
$$;
create function public.heartbeat_processing_job(p_user_id uuid, p_job_id uuid, p_lease uuid)
returns setof public.jobs language plpgsql security definer set search_path = public as $$
begin
  return query update public.jobs set heartbeat_at = now(), lease_expires_at = now() + interval '60 seconds'
    where id = p_job_id and user_id = p_user_id and lease_token = p_lease and status = 'processing'
      and lease_expires_at > now() returning *;
end;
$$;
create function public.set_processing_stage(p_user_id uuid, p_job_id uuid, p_lease uuid,
 p_stage text, p_status public.item_status default 'processing')
returns setof public.jobs language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  update public.jobs set processing_stage = p_stage, status = p_status, updated_at = now(),
   lease_token = case when p_status = 'processing' then lease_token else null end,
   lease_expires_at = case when p_status = 'processing' then lease_expires_at else null end
   where id = p_job_id and user_id = p_user_id and lease_token = p_lease and lease_expires_at > now()
   returning * into j;
  if not found then return; end if;
  update public.items set processing_stage = p_stage, status = p_status, failure_reason = case when p_status in ('failed', 'awaiting_manual_content') then p_stage else null end,
    updated_at = now() where id = j.item_id and user_id = p_user_id;
  return next j;
end;
$$;
create function public.save_job_source(p_user_id uuid, p_job_id uuid, p_lease uuid, p_text text)
returns setof public.jobs language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  select * into j from public.jobs where id = p_job_id and user_id = p_user_id and lease_token = p_lease and lease_expires_at > now() for update;
  if not found then return; end if;
  if length(trim(p_text)) < 200 or octet_length(p_text) > 100000 then raise exception 'invalid_content'; end if;
  insert into public.source_contents(item_id, user_id, acquisition_method, content, content_hash)
    values (j.item_id, p_user_id, 'fetch', p_text, encode(digest(p_text, 'sha256'), 'hex'))
    on conflict (item_id) do update set content = excluded.content, content_hash = excluded.content_hash
      where source_contents.user_id = p_user_id;
  if not found then raise exception 'source_owner_mismatch'; end if;
  return next j;
end;
$$;
create function public.record_model_result(p_user_id uuid, p_job_id uuid, p_lease uuid, p_reservation uuid, p_result jsonb, p_generation text)
returns setof public.jobs language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  -- Persist the generation identifier even if the execution lease was lost: charges must be reconcilable.
  update public.usage_reservations u set generation_id = p_generation
    where u.id = p_reservation and (u.job_id = p_job_id or u.job_id is null) and u.user_id = p_user_id
    and u.generation_id is null;
  update public.jobs set model_result = p_result, updated_at = now() where id = p_job_id and user_id = p_user_id
    and reservation_id = p_reservation and lease_token = p_lease and lease_expires_at > now() returning * into j;
  if found then return next j; end if;
end;
$$;
create function public.complete_processing_job(p_user_id uuid, p_job_id uuid, p_lease uuid, p_assessment jsonb, p_citations jsonb)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare j public.jobs; a uuid; c jsonb;
begin
  select * into j from public.jobs where id = p_job_id and user_id = p_user_id and lease_token = p_lease and lease_expires_at > now() for update;
  if not found then return; end if;
  if not exists (select 1 from public.source_contents where item_id = j.item_id and user_id = p_user_id)
    or not exists (select 1 from public.usage_reservations where id = j.reservation_id and user_id = p_user_id and state = 'settled') then return; end if;
  insert into public.assessments(item_id, user_id, note, criteria, score, verdict, threshold_snapshot)
    values (j.item_id, p_user_id, p_assessment->>'note', p_assessment->'criteria', (p_assessment->>'score')::numeric,
    (p_assessment->>'verdict')::public.verdict, j.threshold_snapshot) returning id into a;
  for c in select * from jsonb_array_elements(p_citations) loop
    insert into public.citations(id, assessment_id, user_id, excerpt, start_position, end_position, source_url)
      values ((c->>'id')::uuid, a, p_user_id, c->>'excerpt', (c->>'start_position')::int, (c->>'end_position')::int, c->>'source_url');
  end loop;
  update public.jobs set status = 'completed', processing_stage = 'completed', model_result = null, lease_token = null, lease_expires_at = null, updated_at = now() where id = j.id;
  return query update public.items set status = 'completed', processing_stage = 'completed', failure_reason = null, updated_at = now()
    where items.id = j.item_id and items.user_id = p_user_id returning *;
end;
$$;

create function public.paste_item_content(p_user_id uuid, p_text text, p_item_id uuid default null)
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
    values (i.id, p_user_id, 'paste', p_text, encode(digest(p_text, 'sha256'), 'hex'))
    on conflict (item_id) do update set acquisition_method = 'paste', content = excluded.content, content_hash = excluded.content_hash
      where source_contents.user_id = p_user_id;
  if not found then raise exception 'source_owner_mismatch'; end if;
  return next i;
end;
$$;
create function public.resume_processing_item(p_user_id uuid, p_item_id uuid)
returns setof public.items language plpgsql security definer set search_path = public as $$
declare j public.jobs;
begin
  select * into j from public.jobs where item_id = p_item_id and user_id = p_user_id and status = 'failed'
    and processing_stage in ('budget_exhausted', 'not_configured', 'invalid_model_output', 'provider_rejected') for update;
  if not found then return; end if;
  if exists (select 1 from public.usage_reservations where id = j.reservation_id and state = 'reserved') then return; end if;
  update public.jobs set status = 'queued', processing_stage = 'queued', reservation_id = null, model_result = null,
    threshold_snapshot = null, lease_token = null, lease_expires_at = null where id = j.id;
  return query update public.items set status = 'queued', processing_stage = 'queued', failure_reason = null, updated_at = now()
    where id = p_item_id and user_id = p_user_id and expires_at > now() returning *;
end;
$$;
create function public.list_processing_items(p_user_id uuid)
returns table (id uuid, user_id uuid, original_url text, title text, status public.item_status, unread boolean,
 processing_stage text, failure_reason text, updated_at timestamptz, score numeric, verdict public.verdict, worker_active boolean)
language sql security definer set search_path = public as $$
 select i.id, i.user_id, i.original_url, i.title, i.status, i.unread, i.processing_stage, i.failure_reason, i.updated_at, a.score, a.verdict,
  coalesce(j.status = 'processing' and j.heartbeat_at > now() - interval '45 seconds' and j.lease_expires_at > now(), false)
 from public.items i left join public.assessments a on a.item_id = i.id and a.user_id = p_user_id
 left join public.jobs j on j.item_id = i.id and j.user_id = p_user_id
 where i.user_id = p_user_id and i.expires_at > now() order by i.unread desc, a.score desc nulls last, i.created_at desc limit 50;
$$;
create function public.cleanup_processing_data(p_user_id uuid)
returns setof public.settings language plpgsql security definer set search_path = public as $$
begin
  delete from public.items where user_id = p_user_id and expires_at < now();
  delete from public.usage_reservations where user_id = p_user_id and state = 'settled' and created_at < now() - interval '30 days';
  delete from public.usage_months m where m.user_id = p_user_id and m.month < date_trunc('month', now() at time zone 'UTC')::date
    and not exists (select 1 from public.usage_reservations r where r.user_id = p_user_id and r.month = m.month and r.state = 'reserved');
  return;
end;
$$;

-- Harden legacy RPCs too: every server-side mutation is callable only with the backend key.
revoke execute on function public.claim_next_job(uuid) from public, anon, authenticated;
grant execute on function public.claim_next_job(uuid) to service_role;
do $$
declare f record;
begin
 for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname in ('get_user_settings','update_user_threshold','set_user_budget',
  'get_usage_summary','reserve_analysis','settle_analysis','claim_processing_job','set_processing_stage',
  'save_job_source','record_model_result','complete_processing_job','paste_item_content','resume_processing_item',
  'list_processing_items','cleanup_processing_data','heartbeat_processing_job') loop
  execute format('revoke execute on function %s from public, anon, authenticated', f.signature);
  execute format('grant execute on function %s to service_role', f.signature);
 end loop;
end;
$$;
