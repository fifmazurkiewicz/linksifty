begin;
select plan(12);
insert into auth.users(id,email) values
 ('88888888-8888-4888-8888-888888888888','duplicate1@example.test'),
 ('99999999-9999-4999-8999-999999999999','duplicate2@example.test');
select public.get_or_create_account_profile('88888888-8888-4888-8888-888888888888','duplicate1@example.test',false);
select public.get_or_create_account_profile('99999999-9999-4999-8999-999999999999','duplicate2@example.test',true);
select public.submit_fetch_items('88888888-8888-4888-8888-888888888888',array['https://example.test/article#one']);
select throws_ok($$select public.submit_fetch_items('88888888-8888-4888-8888-888888888888',array['https://example.test/article#two'])$$,'P0001','duplicate_link','fragment variation is blocked before creating a job');
select is((select count(*)::int from public.items where user_id='88888888-8888-4888-8888-888888888888'),1,'duplicate creates no extra item');
select is((select trial_links_used from public.account_profiles where user_id='88888888-8888-4888-8888-888888888888'),1,'duplicate consumes no trial');
select throws_ok($$select public.submit_search_items('88888888-8888-4888-8888-888888888888',array['https://EXAMPLE.test:443/article'])$$,'P0001','duplicate_link','search submission shares duplicate guard');
select throws_ok($$select public.submit_fetch_items('88888888-8888-4888-8888-888888888888',array['https://fresh.test/page','https://fresh.test/page#anchor'])$$,'P0001','duplicate_link','same-batch duplicate rejects the entire batch');
select is((select count(*)::int from public.items where user_id='88888888-8888-4888-8888-888888888888'),1,'rejected batch creates no partial items');
select lives_ok($$select public.submit_fetch_items('99999999-9999-4999-8999-999999999999',array['https://example.test/article'])$$,'other owner can independently save the URL');
select lives_ok($$select public.submit_fetch_items('88888888-8888-4888-8888-888888888888',array['https://example.test/article?id=1'])$$,'meaningful query parameter is preserved');
update public.items set expires_at=now()-interval '1 second' where user_id='88888888-8888-4888-8888-888888888888' and original_url like '%#one';
select lives_ok($$select public.submit_fetch_items('88888888-8888-4888-8888-888888888888',array['https://example.test/article'])$$,'expired URL can be submitted again');
insert into public.items(id,user_id,original_url,canonical_url,input_mode,status,processing_stage)
 values('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','99999999-9999-4999-8999-999999999999','https://example.test/article#legacy','https://example.test/article#legacy','fetch','failed','invalid_model_output');
insert into public.jobs(item_id,user_id,status,processing_stage)
 values('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','99999999-9999-4999-8999-999999999999','failed','invalid_model_output');
select throws_ok($$select public.resume_processing_item('99999999-9999-4999-8999-999999999999','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')$$,'P0001','duplicate_link','legacy duplicate cannot resume alongside an active URL');
set local role authenticated;
select throws_ok($$select public.submit_fetch_items('88888888-8888-4888-8888-888888888888',array['https://bypass.test'])$$,'42501',null,'guarded submission remains server-only');
select throws_ok($$select public.resume_processing_item('99999999-9999-4999-8999-999999999999','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')$$,'42501',null,'guarded resume remains server-only');
reset role;
select * from finish();
rollback;
