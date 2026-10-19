-- One additional, explicit evidence-gap search. Never reuse a paid call slot.
-- Apply before the matching backend and frontend. Old executors stay compatible.
alter table public.usage_reservations drop constraint usage_reservations_chat_slot_check;
alter table public.usage_reservations add constraint usage_reservations_chat_slot_check
  check (chat_slot in ('classification','decision','search','answer','search_refined','answer_final'));

-- Three answer generations and two bounded page-fetch batches can exceed five minutes.
alter table public.chat_turns alter column deadline set default now()+interval '8 minutes';

create or replace function public.reserve_chat_call(p_user_id uuid,p_turn_id uuid,p_slot text,p_amount numeric)
returns table (id uuid) language plpgsql security definer set search_path=public as $$
declare t public.chat_turns; b numeric; s numeric; pending numeric;
  m date := date_trunc('month',now() at time zone 'UTC')::date; reservation uuid;
begin
  if p_slot is null or p_slot not in ('classification','decision','search','answer','search_refined','answer_final')
    or p_amount is null or p_amount<=0 or p_amount>1000000
    then raise exception 'invalid_reservation' using errcode='22023'; end if;
  perform 1 from public.account_profiles where user_id=p_user_id and status<>'rejected' for update;
  if not found then return; end if;
  select monthly_budget_usd into b from public.settings where user_id=p_user_id for update;
  if not found then return; end if;
  select * into t from public.chat_turns where chat_turns.id=p_turn_id and user_id=p_user_id
    and status='pending' and deadline>now() for update;
  if not found or not exists(select 1 from public.items where items.id=t.item_id
    and user_id=p_user_id and expires_at>now() and status='completed') then return; end if;
  -- Unique slots are never returned to a second executor, even after settlement.
  if exists(select 1 from public.usage_reservations where chat_turn_id=t.id and chat_slot=p_slot)
    then return; end if;
  if p_slot='decision' and not exists(select 1 from public.usage_reservations
    where chat_turn_id=t.id and chat_slot='classification') then return; end if;
  if p_slot='search' and not exists(select 1 from public.usage_reservations
    where chat_turn_id=t.id and chat_slot='decision') then return; end if;
  if p_slot='answer' and not exists(select 1 from public.usage_reservations
    where chat_turn_id=t.id and chat_slot='search') then return; end if;
  if p_slot='search_refined' and (
    not exists(select 1 from public.usage_reservations
      where chat_turn_id=t.id and chat_slot='search' and state='settled')
    or not exists(select 1 from public.usage_reservations
      where chat_turn_id=t.id and chat_slot='answer')) then return; end if;
  if p_slot='answer_final' and not exists(select 1 from public.usage_reservations
    where chat_turn_id=t.id and chat_slot='search_refined') then return; end if;
  insert into public.usage_months(user_id,month) values(p_user_id,m) on conflict do nothing;
  select spent_usd into s from public.usage_months where user_id=p_user_id and month=m;
  select coalesce(sum(amount_usd),0) into pending from public.usage_reservations
    where user_id=p_user_id and state='reserved';
  if s+pending+p_amount>b then return; end if;
  insert into public.usage_reservations(user_id,month,amount_usd,provider,chat_turn_id,chat_slot)
    values(p_user_id,m,p_amount,
      case when p_slot in ('search','search_refined') then 'brave' else 'openrouter' end,t.id,p_slot)
    returning usage_reservations.id into reservation;
  return query select reservation;
end;
$$;

create or replace function public.record_chat_generation(p_user_id uuid,p_reservation uuid,p_generation text)
returns setof public.usage_reservations language plpgsql security definer set search_path=public as $$
begin
  -- Final-answer generation IDs also survive content deletion for reconciliation.
  if p_generation is not null and length(p_generation) between 1 and 200 then
    return query update public.usage_reservations set generation_id=p_generation
      where user_id=p_user_id and id=p_reservation
      and chat_slot in ('classification','decision','answer','answer_final')
      and (generation_id is null or generation_id=p_generation) returning *;
  end if;
end;
$$;

-- CREATE OR REPLACE preserves the existing service-role-only grants.
notify pgrst, 'reload schema';
