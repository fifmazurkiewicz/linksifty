-- Durable per-question execution. All calls share the existing USD ledger.
create unique index items_id_owner on public.items(id,user_id);
create table public.chat_turns (
  id uuid primary key,
  item_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  question text not null check (length(btrim(question)) between 1 and 4000 and octet_length(question)<=16000),
  status text not null default 'pending' check (status in ('pending','completed','failed')),
  answer jsonb not null default '[]' check (jsonb_typeof(answer)='array' and octet_length(answer::text)<=150000),
  insufficient boolean not null default false,
  search_status text not null default 'not_needed',
  error text,
  sources jsonb not null default '[]' check (jsonb_typeof(sources)='array' and octet_length(sources::text)<=1500000),
  created_at timestamptz not null default now(),
  deadline timestamptz not null default now()+interval '5 minutes',
  foreign key (item_id,user_id) references public.items(id,user_id) on delete cascade
);
create unique index one_pending_item_chat on public.chat_turns(item_id) where status='pending';
create index chat_turns_owner_item on public.chat_turns(user_id,item_id,created_at);
create unique index chat_turns_id_owner on public.chat_turns(id,user_id);
alter table public.chat_turns enable row level security;
create policy "chat turns owner read" on public.chat_turns for select
  using (auth.uid()=user_id and exists(select 1 from public.items i
    where i.id=item_id and i.user_id=auth.uid() and i.expires_at>now()));
revoke all on public.chat_turns from public,anon,authenticated;
grant select on public.chat_turns to authenticated;
grant all on public.chat_turns to service_role;

-- The turn FK detaches on deletion, leaving only non-content billing metadata.
alter table public.usage_reservations add column chat_turn_id uuid;
alter table public.usage_reservations add foreign key (chat_turn_id,user_id)
  references public.chat_turns(id,user_id) on delete set null (chat_turn_id);
alter table public.usage_reservations add column chat_slot text
  check (chat_slot in ('decision','search','answer'));
create unique index one_call_per_chat_slot on public.usage_reservations(chat_turn_id,chat_slot);

create function public.begin_chat_turn(p_user_id uuid,p_item_id uuid,p_request_id uuid,p_question text)
returns table (turn jsonb,claimed boolean)
language plpgsql security definer set search_path=public as $$
declare t public.chat_turns;
begin
  if p_request_id is null or p_question is null or length(btrim(p_question)) not between 1 and 4000
    or octet_length(p_question)>16000 then raise exception 'invalid_question' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  perform public.get_user_settings(p_user_id);
  perform 1 from public.settings where user_id=p_user_id for update;
  perform 1 from public.items i where i.id=p_item_id and i.user_id=p_user_id
    and i.status='completed' and i.expires_at>now() for update;
  if not found or not exists(select 1 from public.source_contents where item_id=p_item_id and user_id=p_user_id)
    or not exists(select 1 from public.assessments where item_id=p_item_id and user_id=p_user_id) then return; end if;
  update public.chat_turns set status='failed',error='interrupted'
    where user_id=p_user_id and item_id=p_item_id and status='pending' and deadline<now();
  select * into t from public.chat_turns where id=p_request_id and user_id=p_user_id and item_id=p_item_id;
  if found then return query select to_jsonb(t),false; return; end if;
  if exists(select 1 from public.chat_turns where item_id=p_item_id and status='pending') then return; end if;
  insert into public.chat_turns(id,item_id,user_id,question)
    values(p_request_id,p_item_id,p_user_id,p_question) on conflict do nothing returning * into t;
  if found then return query select to_jsonb(t),true; end if;
end;
$$;

create function public.list_chat_turns(p_user_id uuid,p_item_id uuid)
returns setof public.chat_turns language plpgsql security definer set search_path=public as $$
begin
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  if not exists(select 1 from public.items where id=p_item_id and user_id=p_user_id
    and status='completed' and expires_at>now()) then return; end if;
  update public.chat_turns set status='failed',error='interrupted'
    where user_id=p_user_id and item_id=p_item_id and status='pending' and deadline<now();
  return query select recent.* from (select * from public.chat_turns
    where user_id=p_user_id and item_id=p_item_id order by created_at desc,id desc limit 100) recent
    order by recent.created_at,recent.id;
end;
$$;

create function public.reserve_chat_call(p_user_id uuid,p_turn_id uuid,p_slot text,p_amount numeric)
returns table (id uuid) language plpgsql security definer set search_path=public as $$
declare t public.chat_turns; b numeric; s numeric; pending numeric;
  m date := date_trunc('month',now() at time zone 'UTC')::date; reservation uuid;
begin
  if p_slot is null or p_slot not in ('decision','search','answer') or p_amount is null
    or p_amount<=0 or p_amount>1000000 then raise exception 'invalid_reservation' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  if not found then return; end if;
  select * into t from public.chat_turns where chat_turns.id=p_turn_id and user_id=p_user_id
    and status='pending' and deadline>now() for update;
  if not found or not exists(select 1 from public.items where items.id=t.item_id
    and user_id=p_user_id and expires_at>now() and status='completed') then return; end if;
  -- Never return an existing call slot to an executor: an uncertain call is not retried.
  if exists(select 1 from public.usage_reservations where chat_turn_id=t.id and chat_slot=p_slot)
    then return; end if;
  if p_slot='answer' and not exists(select 1 from public.usage_reservations
    where chat_turn_id=t.id and chat_slot='search') then return; end if;
  if p_slot='search' and not exists(select 1 from public.usage_reservations
    where chat_turn_id=t.id and chat_slot='decision') then return; end if;
  insert into public.usage_months(user_id,month) values(p_user_id,m) on conflict do nothing;
  select spent_usd into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then return; end if;
  insert into public.usage_reservations(user_id,month,amount_usd,provider,chat_turn_id,chat_slot)
    values(p_user_id,m,p_amount,case when p_slot='search' then 'brave' else 'openrouter' end,t.id,p_slot)
    returning usage_reservations.id into reservation;
  return query select reservation;
end;
$$;

create function public.record_chat_generation(p_user_id uuid,p_reservation uuid,p_generation text)
returns setof public.usage_reservations language plpgsql security definer set search_path=public as $$
begin
  -- Survives content deletion. A first generation ID cannot be overwritten.
  if p_generation is not null and length(p_generation) between 1 and 200 then
    return query update public.usage_reservations set generation_id=p_generation
      where user_id=p_user_id and id=p_reservation and chat_slot in ('decision','answer')
      and (generation_id is null or generation_id=p_generation) returning *;
  end if;
end;
$$;

create function public.finish_chat_turn(p_user_id uuid,p_turn_id uuid,p_result jsonb)
returns setof public.chat_turns language plpgsql security definer set search_path=public as $$
begin
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  if p_result->>'status' is null or p_result->>'status' not in ('completed','failed')
    or jsonb_typeof(p_result->'answer') is distinct from 'array'
    or jsonb_typeof(p_result->'sources') is distinct from 'array'
    then raise exception 'invalid_chat_result' using errcode='22023'; end if;
  return query update public.chat_turns t set
    status=p_result->>'status',answer=p_result->'answer',
    insufficient=coalesce((p_result->>'insufficient')::boolean,false),
    search_status=coalesce(p_result->>'search_status','not_needed'),
    sources=p_result->'sources',error=p_result->>'error'
    where t.id=p_turn_id and t.user_id=p_user_id and t.status='pending' and t.deadline>now()
    and exists(select 1 from public.items i where i.id=t.item_id and i.user_id=p_user_id
      and i.expires_at>now() and i.status='completed') returning t.*;
end;
$$;

do $$
declare f record;
begin
 for f in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname in ('begin_chat_turn','list_chat_turns',
    'reserve_chat_call','record_chat_generation','finish_chat_turn') loop
  execute format('revoke execute on function %s from public,anon,authenticated',f.signature);
  execute format('grant execute on function %s to service_role',f.signature);
 end loop;
end;
$$;
notify pgrst, 'reload schema';
