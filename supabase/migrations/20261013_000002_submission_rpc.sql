-- Server-only RPCs: authenticated users must go through the owner-scoped API.
revoke execute on function public.claim_next_job(uuid) from public, anon, authenticated;
grant execute on function public.claim_next_job(uuid) to service_role;

create function public.submit_fetch_items(p_user_id uuid, p_urls text[])
returns setof public.items
language plpgsql security definer set search_path = public as $$
declare submitted public.items; source_url text;
begin
  if p_user_id is null or cardinality(p_urls) is null or cardinality(p_urls) not between 1 and 5 then
    raise exception 'A user and one to five URLs are required';
  end if;
  foreach source_url in array p_urls loop
    if source_url is null or source_url !~ '^https?://' then
      raise exception 'Only HTTP and HTTPS URLs are accepted';
    end if;
    insert into public.items(user_id, original_url, canonical_url, input_mode, title)
      values(p_user_id, source_url, source_url, 'fetch', source_url) returning * into submitted;
    insert into public.jobs(user_id, item_id) values(p_user_id, submitted.id);
    return next submitted;
  end loop;
end;
$$;
revoke execute on function public.submit_fetch_items(uuid, text[]) from public, anon, authenticated;
grant execute on function public.submit_fetch_items(uuid, text[]) to service_role;
