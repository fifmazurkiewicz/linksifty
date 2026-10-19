-- Titles are metadata: invalid assessments must not discard a valid topic title.
create function public.valid_item_title(p_title text)
returns boolean language sql immutable set search_path=public as $$
  select p_title is not null and length(btrim(p_title)) between 1 and 160
    and p_title !~ '[[:cntrl:]]';
$$;

create or replace function public.record_model_result(
  p_user_id uuid,p_job_id uuid,p_lease uuid,p_reservation uuid,p_result jsonb,p_generation text
) returns setof public.jobs language plpgsql security definer set search_path=public as $$
declare j public.jobs;
begin
  -- Preserve late billing metadata, even after content deletion or lease loss.
  update public.usage_reservations u set generation_id=p_generation
    where u.id=p_reservation and (u.job_id=p_job_id or u.job_id is null) and u.user_id=p_user_id
      and u.generation_id is null;
  update public.jobs set model_result=p_result,updated_at=now()
    where id=p_job_id and user_id=p_user_id and reservation_id=p_reservation
      and lease_token=p_lease and lease_expires_at>now() and status='processing'
    returning * into j;
  if not found then return; end if;
  if public.valid_item_title(p_result->>'title') then
    update public.items set title=btrim(p_result->>'title'),updated_at=now()
      where id=j.item_id and user_id=p_user_id and expires_at>now()
        and (title is null or title=original_url or title='Pasted content');
  end if;
  return next j;
end;
$$;

-- Reuse the USD ledger, with a detached non-content record after deletion.
alter table public.usage_reservations drop constraint usage_reservations_purpose_check;
alter table public.usage_reservations add constraint usage_reservations_purpose_check
  check (purpose in ('analysis','image_extraction','source_selection','title'));
alter table public.usage_reservations add column title_item_id uuid;
alter table public.usage_reservations add foreign key (title_item_id,user_id)
  references public.items(id,user_id) on delete set null (title_item_id);
create unique index one_reserved_item_title on public.usage_reservations(title_item_id)
  where state='reserved' and title_item_id is not null;

create function public.reserve_item_title(p_user_id uuid,p_item_id uuid,p_amount numeric)
returns table(id uuid,text text) language plpgsql security definer set search_path=public as $$
declare i public.items; content_text text; b numeric; s numeric; pending numeric; reservation uuid;
  m date:=date_trunc('month',now() at time zone 'UTC')::date;
begin
  if p_amount is null or p_amount<=0 or p_amount>1000000 then
    raise exception 'invalid_reservation' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  perform public.get_user_settings(p_user_id);
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  -- The settings lock serializes admission with other calls and settlement.
  if exists(select 1 from public.usage_reservations where user_id=p_user_id
    and title_item_id=p_item_id and state='reserved') then return; end if;
  perform 1 from public.jobs where item_id=p_item_id and user_id=p_user_id for update;
  select * into i from public.items where items.id=p_item_id and user_id=p_user_id
    and expires_at>now() and status not in ('queued','processing') for update;
  if not found or (i.title is not null and i.title is distinct from i.original_url
    and i.title<>'Pasted content') then return; end if;
  select content into content_text from public.source_contents where item_id=p_item_id and user_id=p_user_id;
  if content_text is null or length(btrim(content_text))<200 or octet_length(content_text)>100000 then return; end if;
  insert into public.usage_months(user_id,month) values(p_user_id,m) on conflict do nothing;
  select spent_usd into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then return; end if;
  insert into public.usage_reservations(user_id,month,amount_usd,provider,purpose,title_item_id)
    values(p_user_id,m,p_amount,'openrouter','title',p_item_id) returning usage_reservations.id into reservation;
  return query select reservation,content_text;
end;
$$;

create function public.record_item_title(
  p_user_id uuid,p_item_id uuid,p_reservation uuid,p_title text,p_generation text
) returns setof public.items language plpgsql security definer set search_path=public as $$
declare reservation public.usage_reservations;
begin
  perform 1 from public.account_profiles where user_id=p_user_id for update;
  -- Billing IDs survive deletion and rejection; title writes still require live ownership.
  update public.usage_reservations set generation_id=p_generation
    where user_id=p_user_id and id=p_reservation and purpose='title'
      and (title_item_id=p_item_id or title_item_id is null) and generation_id is null;
  if not exists(select 1 from public.account_profiles where user_id=p_user_id and status<>'rejected') then return; end if;
  select * into reservation from public.usage_reservations where id=p_reservation
    and user_id=p_user_id and title_item_id=p_item_id and purpose='title' and state='reserved';
  if not found or not public.valid_item_title(p_title) then return; end if;
  return query update public.items set title=btrim(p_title),updated_at=now()
    where items.id=p_item_id and user_id=p_user_id and expires_at>now()
      and status not in ('queued','processing')
      and (title is null or title=original_url or title='Pasted content') returning items.*;
end;
$$;

do $$
declare f record;
begin
  for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname in ('valid_item_title','record_model_result','reserve_item_title','record_item_title') loop
    execute format('revoke execute on function %s from public,anon,authenticated',f.signature);
    execute format('grant execute on function %s to service_role',f.signature);
  end loop;
end;
$$;
notify pgrst,'reload schema';
