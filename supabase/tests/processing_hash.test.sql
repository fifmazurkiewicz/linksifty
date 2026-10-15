-- Supabase preinstalls pgcrypto under extensions, outside the RPC search_path.
begin;
select plan(6);
create schema if not exists extensions;
do $$
begin
  if (select n.nspname from pg_extension e join pg_namespace n on n.oid=e.extnamespace where e.extname='pgcrypto') <> 'extensions' then
    alter extension pgcrypto set schema extensions;
  end if;
end;
$$;
insert into auth.users(id,email) values
 ('55555555-5555-4555-8555-555555555555','hash@example.test');
select public.get_or_create_account_profile('55555555-5555-4555-8555-555555555555','hash@example.test',true);
set local role service_role;
select lives_ok($$select public.paste_item_content('55555555-5555-4555-8555-555555555555',repeat('Zażółć gęślą jaźń ',30))$$,'pasted source works with pgcrypto outside public');
select is((select content_hash from public.source_contents where user_id='55555555-5555-4555-8555-555555555555'),
 encode(pg_catalog.sha256(convert_to(repeat('Zażółć gęślą jaźń ',30),'UTF8')),'hex'),'pasted UTF8 source has correct SHA256');
select public.submit_fetch_items('55555555-5555-4555-8555-555555555555',array['https://hash.example']);
-- Claim both jobs: only the URL job is used for the fetched-source path.
create temporary table hash_jobs as select * from public.claim_processing_job('55555555-5555-4555-8555-555555555555');
insert into hash_jobs select * from public.claim_processing_job('55555555-5555-4555-8555-555555555555');
select lives_ok(format('select public.save_job_source(%L,%L,%L,%L)',user_id,id,lease_token,repeat('Zażółć gęślą jaźń ',30)),'fetched source works with pgcrypto outside public') from hash_jobs where original_url is not null;
select is((select count(*)::int from public.source_contents where user_id='55555555-5555-4555-8555-555555555555'),2,'both pasted and fetched source are saved');
select is((select content_hash from public.source_contents where item_id=(select item_id from hash_jobs where original_url is not null)),
 encode(pg_catalog.sha256(convert_to(repeat('Zażółć gęślą jaźń ',30),'UTF8')),'hex'),'fetched UTF8 source has correct SHA256');
reset role;
set local role authenticated;
select throws_ok($$select public.paste_item_content('55555555-5555-4555-8555-555555555555',repeat('source ',40))$$,'42501',null,'replacement preserves server-only mutation permission');
reset role;
select * from finish();
rollback;
