-- Explicit text-only fetch scope. NULL retains unknown historical/manual scope.
alter table public.source_contents add column omitted_media text[]
  check (omitted_media is null or (cardinality(omitted_media)<=5
    and array_position(omitted_media,null) is null
    and omitted_media <@ array['image','video','gif','audio','attachment']::text[]));

create function public.save_text_job_source(
  p_user_id uuid,p_job_id uuid,p_lease uuid,p_text text,p_media_types text[]
) returns setof public.jobs language plpgsql security definer set search_path=public as $$
declare j public.jobs;
begin
  if p_media_types is null or cardinality(p_media_types)>5 or array_position(p_media_types,null) is not null
    or not p_media_types <@ array['image','video','gif','audio','attachment']::text[]
    then raise exception 'invalid_media_scope'; end if;
  perform 1 from public.account_profiles p where p.user_id=p_user_id and p.status<>'rejected' for update;
  if not found then return; end if;
  select q.* into j from public.jobs q join public.items i on i.id=q.item_id and i.user_id=q.user_id
    where q.id=p_job_id and q.user_id=p_user_id and q.lease_token=p_lease
    and q.lease_expires_at>now() and q.status='processing' and i.expires_at>now()
    for update of q;
  if not found then return; end if;
  if p_text is null or length(trim(p_text))<200 or octet_length(p_text)>100000
    then raise exception 'invalid_content'; end if;
  insert into public.source_contents(item_id,user_id,acquisition_method,content,content_hash,omitted_media)
    values(j.item_id,p_user_id,'fetch',p_text,
      pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p_text,'UTF8')),'hex'),p_media_types)
    on conflict(item_id) do update set acquisition_method='fetch',content=excluded.content,
      content_hash=excluded.content_hash,omitted_media=excluded.omitted_media
    where source_contents.user_id=p_user_id;
  if not found then raise exception 'source_owner_mismatch'; end if;
  return next j;
end;
$$;
revoke execute on function public.save_text_job_source(uuid,uuid,uuid,text,text[]) from public,anon,authenticated;
grant execute on function public.save_text_job_source(uuid,uuid,uuid,text,text[]) to service_role;
notify pgrst,'reload schema';
