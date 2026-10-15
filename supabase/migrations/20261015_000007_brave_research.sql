-- Opt-in source discovery, exact configured search charges and redacted diagnostics.
alter table public.jobs add column web_search boolean not null default false;
alter table public.jobs add column search_reservation_id uuid references public.usage_reservations(id) on delete set null;
alter table public.jobs add column search_context jsonb;
alter table public.usage_reservations add column provider text not null default 'openrouter' check (provider in ('openrouter','brave'));
alter table public.citations add column source_id text not null default 'primary';
drop index public.one_active_job_reservation;
create unique index one_active_job_provider_reservation on public.usage_reservations(job_id,provider) where state='reserved';

create function public.submit_search_items(p_user_id uuid, p_urls text[])
returns setof public.items language plpgsql security definer set search_path=public as $$
declare i public.items;
begin
  for i in select * from public.submit_fetch_items(p_user_id,p_urls) loop
    update public.jobs set web_search=true where item_id=i.id and user_id=p_user_id;
    return next i;
  end loop;
end;
$$;
create function public.reserve_web_search(p_user_id uuid,p_job_id uuid,p_lease uuid,p_amount numeric)
returns setof public.usage_reservations language plpgsql security definer set search_path=public as $$
declare j public.jobs; r public.usage_reservations; b numeric; s numeric; pending numeric;
 m date := date_trunc('month',now() at time zone 'UTC')::date;
begin
  if p_amount is null or p_amount <= 0 or p_amount > 1000000 then raise exception 'invalid_reservation'; end if;
  perform public.get_user_settings(p_user_id);
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  select * into j from public.jobs where id=p_job_id and user_id=p_user_id and lease_token=p_lease
   and lease_expires_at>now() and status='processing' and web_search=true for update;
  if not found or j.search_reservation_id is not null then return; end if;
  if not exists(select 1 from public.account_profiles where user_id=p_user_id and status<>'rejected') then return; end if;
  select coalesce(sum(spent_usd),0) into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then return; end if;
  insert into public.usage_reservations(user_id,job_id,month,amount_usd,provider)
   values(p_user_id,p_job_id,m,p_amount,'brave') returning * into r;
  update public.jobs set search_reservation_id=r.id where id=j.id;
  return next r;
end;
$$;
create function public.save_research_context(p_user_id uuid,p_job_id uuid,p_lease uuid,p_context jsonb)
returns setof public.jobs language plpgsql security definer set search_path=public as $$
begin
  if p_context is null or jsonb_typeof(p_context->'sources') is distinct from 'array' or jsonb_array_length(p_context->'sources')>5 or octet_length(p_context::text)>300000 then raise exception 'invalid_research_context'; end if;
  if p_context->>'status' not in ('not_requested','unavailable','uncertain','budget_exhausted','no_sources','ready')
    or exists(select 1 from jsonb_array_elements(p_context->'sources') s where s->>'id' is null or s->>'id'='primary'
      or s->>'url' !~ '^https?://' or length(s->>'text') not between 1 and 12000)
    or (select count(*) from jsonb_array_elements(p_context->'sources')) <> (select count(distinct s->>'id') from jsonb_array_elements(p_context->'sources') s)
    then raise exception 'invalid_research_context'; end if;
  return query update public.jobs set search_context=p_context,updated_at=now()
   where id=p_job_id and user_id=p_user_id and lease_token=p_lease and lease_expires_at>now() and status='processing' and search_context is null returning *;
end;
$$;
-- Return shape changes require replacing the function, then restoring its grants.
drop function public.claim_processing_job(uuid);
create function public.claim_processing_job(p_user_id uuid)
returns table (id uuid, item_id uuid, user_id uuid, lease_token uuid, original_url text, source_text text,
 threshold_snapshot numeric, reservation_id uuid, generation_id text, actual_usd numeric, reservation_state text, model_result jsonb, web_search boolean, search_reservation_id uuid, search_context jsonb)
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
    j.threshold_snapshot, j.reservation_id, u.generation_id, u.actual_usd, u.state, j.model_result, j.web_search, j.search_reservation_id, j.search_context
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
  insert into public.assessments(item_id, user_id, note, criteria, score, verdict, threshold_snapshot)
    values (j.item_id, p_user_id, p_assessment->>'note', p_assessment->'criteria', (p_assessment->>'score')::numeric,
    (p_assessment->>'verdict')::public.verdict, j.threshold_snapshot) returning id into a;
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

create or replace function public.list_processing_items(p_user_id uuid)
returns table (id uuid, user_id uuid, original_url text, title text, status public.item_status, unread boolean,
 processing_stage text, failure_reason text, updated_at timestamptz, score numeric, verdict public.verdict, worker_active boolean)
language sql security definer set search_path = public as $$
 select i.id, i.user_id, i.original_url, i.title, i.status, i.unread, i.processing_stage, case when i.processing_stage = 'invalid_model_output' then coalesce(j.model_result->>'failure_reason', i.failure_reason) else i.failure_reason end, i.updated_at, a.score, a.verdict,
  coalesce(j.status = 'processing' and j.heartbeat_at > now() - interval '45 seconds' and j.lease_expires_at > now(), false)
 from public.items i left join public.assessments a on a.item_id = i.id and a.user_id = p_user_id
 left join public.jobs j on j.item_id = i.id and j.user_id = p_user_id
 where i.user_id = p_user_id and i.expires_at > now() order by i.unread desc, a.score desc nulls last, i.created_at desc limit 50;
$$;

do $$
declare f record;
begin
 for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('submit_search_items','reserve_web_search','save_research_context','claim_processing_job','complete_processing_job','list_processing_items') loop
  execute format('revoke execute on function %s from public,anon,authenticated',f.signature);
  execute format('grant execute on function %s to service_role',f.signature);
 end loop;
end;
$$;

notify pgrst, 'reload schema';
