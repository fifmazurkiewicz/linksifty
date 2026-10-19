-- Explicit, once-only X reply snapshots. Replies are never assessment evidence.
create table public.item_discussions (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  source_id text not null check (length(source_id) between 1 and 64),
  source_url text not null check (length(source_url) between 1 and 2000),
  post_id text not null check (post_id ~ '^[0-9]{1,19}$'),
  status text not null default 'fetching' check (status in ('fetching','ready','unavailable')),
  replies jsonb not null default '[]'::jsonb
    check (jsonb_typeof(replies)='array' and jsonb_array_length(replies)<=20 and octet_length(replies::text)<=400000),
  created_at timestamptz not null default now(),
  foreign key (item_id,user_id) references public.items(id,user_id) on delete cascade,
  unique (item_id,post_id)
);
alter table public.item_discussions enable row level security;
revoke all on public.item_discussions from public,anon,authenticated;
grant select,insert,update,delete on public.item_discussions to service_role;

create function public.discussion_sources_for_item(p_user_id uuid,p_item_id uuid)
returns table(source_id text,url text) language sql security definer set search_path=public as $$
  with owned as (
    select i.original_url,j.search_context from public.items i
    left join public.jobs j on j.item_id=i.id and j.user_id=p_user_id
    where i.id=p_item_id and i.user_id=p_user_id and i.status='completed' and i.expires_at>now()
      and exists(select 1 from public.account_profiles p where p.user_id=p_user_id and p.status<>'rejected')
  ), candidates as (
    select 'primary'::text as source_id,original_url as url from owned where original_url is not null
    union all
    select s->>'id',s->>'url' from owned,
      lateral jsonb_array_elements(coalesce(search_context->'sources','[]'::jsonb)
        || coalesce(search_context->'discussion_sources','[]'::jsonb)) s
    where s->>'id'<>'primary'
  )
  select distinct on (source_id) source_id,url from candidates
    where length(source_id) between 1 and 64 and length(url) between 1 and 2000
    order by source_id,url;
$$;

create function public.get_item_discussions(p_user_id uuid,p_item_id uuid)
returns table(sources jsonb) language sql security definer set search_path=public as $$
  select coalesce((select jsonb_agg(jsonb_build_object(
      'source_id',s.source_id,'url',s.url,'status',coalesce(d.status,'not_requested'),
      'replies',coalesce(d.replies,'[]'::jsonb)) order by s.source_id)
    from public.discussion_sources_for_item(p_user_id,p_item_id) s
    left join public.item_discussions d on d.item_id=p_item_id and d.user_id=p_user_id
      and s.url ~ '^https?://((www|mobile|m)\.)?(x\.com|twitter\.com)(:(80|443))?/'
      and d.post_id=substring(s.url from '/status/([0-9]{1,19})')), '[]'::jsonb)
  where exists(select 1 from public.items i where i.id=p_item_id and i.user_id=p_user_id
    and i.status='completed' and i.expires_at>now())
    and exists(select 1 from public.account_profiles p where p.user_id=p_user_id and p.status<>'rejected');
$$;

create function public.begin_item_discussion(p_user_id uuid,p_item_id uuid,p_source_id text)
returns table(source_id text,url text,status text,replies jsonb,attempt_id uuid,admitted boolean)
language plpgsql security definer set search_path=public as $$
declare s record; d public.item_discussions; created uuid; post text;
begin
  perform 1 from public.account_profiles p where p.user_id=p_user_id and p.status<>'rejected' for update;
  if not found then return; end if;
  perform 1 from public.items i where i.id=p_item_id and i.user_id=p_user_id
    and i.status='completed' and i.expires_at>now() for update;
  if not found then return; end if;
  select * into s from public.discussion_sources_for_item(p_user_id,p_item_id) where discussion_sources_for_item.source_id=p_source_id;
  if not found or s.url !~ '^https?://((www|mobile|m)\.)?(x\.com|twitter\.com)(:(80|443))?/' then return; end if;
  post:=substring(s.url from '/status/([0-9]{1,19})');
  if post is null then return; end if;
  insert into public.item_discussions(item_id,user_id,source_id,source_url,post_id)
    values(p_item_id,p_user_id,p_source_id,s.url,post)
    on conflict(item_id,post_id) do nothing returning id into created;
  select * into d from public.item_discussions c where c.item_id=p_item_id and c.user_id=p_user_id and c.post_id=post;
  return query select p_source_id,s.url,d.status,d.replies,d.id,created is not null;
end;
$$;

create function public.finish_item_discussion(
  p_user_id uuid,p_item_id uuid,p_attempt_id uuid,p_status text,p_replies jsonb
)
returns table(source_id text,url text,status text,replies jsonb)
language plpgsql security definer set search_path=public as $$
begin
  if p_status is null or p_status not in ('ready','unavailable') or p_replies is null
    or jsonb_typeof(p_replies) is distinct from 'array' or jsonb_array_length(p_replies)>20
    or octet_length(p_replies::text)>400000
    or (p_status='unavailable' and jsonb_array_length(p_replies)<>0) then raise exception 'invalid_discussion'; end if;
  if exists(select 1 from jsonb_array_elements(p_replies) r where
    jsonb_typeof(r) is distinct from 'object'
    or coalesce(r->>'id','') !~ '^[0-9]{1,19}$'
    or coalesce(r->>'author_id','') !~ '^[0-9]{1,19}$'
    or jsonb_typeof(r->'text') is distinct from 'string' or length(btrim(r->>'text')) not between 1 and 4000
    or (r->>'username' is not null and r->>'username' !~ '^[A-Za-z0-9_]{1,15}$')
    or jsonb_typeof(r->'truncated') is distinct from 'boolean'
    or jsonb_typeof(r->'has_media') is distinct from 'boolean') then raise exception 'invalid_discussion'; end if;
  perform 1 from public.account_profiles p where p.user_id=p_user_id and p.status<>'rejected' for update;
  if not found then return; end if;
  perform 1 from public.items i where i.id=p_item_id and i.user_id=p_user_id
    and i.status='completed' and i.expires_at>now() for update;
  if not found then return; end if;
  return query update public.item_discussions d set status=p_status,replies=p_replies
    where d.id=p_attempt_id and d.item_id=p_item_id and d.user_id=p_user_id and d.status='fetching'
    returning d.source_id,d.source_url,d.status,d.replies;
end;
$$;

revoke execute on function public.discussion_sources_for_item(uuid,uuid),public.get_item_discussions(uuid,uuid),
  public.begin_item_discussion(uuid,uuid,text),public.finish_item_discussion(uuid,uuid,uuid,text,jsonb)
  from public,anon,authenticated;
grant execute on function public.discussion_sources_for_item(uuid,uuid),public.get_item_discussions(uuid,uuid),
  public.begin_item_discussion(uuid,uuid,text),public.finish_item_discussion(uuid,uuid,uuid,text,jsonb)
  to service_role;
notify pgrst,'reload schema';
