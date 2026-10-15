begin;
select plan(14);
insert into auth.users(id,email) values ('66666666-6666-4666-8666-666666666666','search@example.test');
select public.get_or_create_account_profile('66666666-6666-4666-8666-666666666666','search@example.test',true);
set local role service_role;
select public.submit_search_items('66666666-6666-4666-8666-666666666666',array['https://primary.example/article']);
create temporary table search_job as select * from public.claim_processing_job('66666666-6666-4666-8666-666666666666');
select is((select web_search from search_job),true,'explicit submission persists search consent');
create temporary table search_res as select r.* from search_job j cross join lateral public.reserve_web_search(j.user_id,j.id,j.lease_token,0.005) r;
select is((select count(*)::int from search_res),1,'search charge reserved atomically');
select is((select provider from search_res),'brave','search provider distinguished from inference');
select is((select count(*)::int from search_job j cross join lateral public.reserve_web_search(j.user_id,j.id,j.lease_token,0.005)),0,'search cannot be automatically reserved again');
select is((select reserved_usd from public.get_usage_summary('66666666-6666-4666-8666-666666666666')),0.005::numeric,'search consumes shared monthly capacity');
select public.settle_analysis(user_id,id,0.005) from search_res;
select public.save_job_source(user_id,id,lease_token,repeat('primary evidence ',40)) from search_job;
select is((select count(*)::int from search_job j cross join lateral public.save_research_context('77777777-7777-4777-8777-777777777777',j.id,j.lease_token,'{"status":"ready","sources":[]}'::jsonb)),0,'foreign owner cannot save research');
select public.save_research_context(user_id,id,lease_token,'{"status":"ready","sources":[{"id":"external-1","url":"https://evidence.example","text":"exact external evidence"}]}'::jsonb) from search_job;
select is((select count(*)::int from search_job j cross join lateral public.save_research_context(j.user_id,j.id,j.lease_token,'{"status":"ready","sources":[]}'::jsonb)),0,'saved source context cannot be replaced');
create temporary table inference_res as select r.* from search_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.14848) r;
select is((select count(*)::int from inference_res),1,'separate model reservation works after search');
select public.settle_analysis(user_id,id,0.001) from inference_res;
select throws_ok(format('select public.complete_processing_job(%L,%L,%L,%L::jsonb,%L::jsonb)',user_id,id,lease_token,
 '{"note":"Result","criteria":[],"score":60,"verdict":"valuable"}',
 '[{"id":"77777777-7777-4777-8777-777777777777","source_id":"external-1","excerpt":"invented evidence","start_position":0,"end_position":17}]'),'P0001','invalid_citation','database rejects a fabricated external quote') from search_job;
select public.complete_processing_job(user_id,id,lease_token,'{"note":"Result","criteria":[],"score":60,"verdict":"valuable"}'::jsonb,
 '[{"id":"77777777-7777-4777-8777-777777777777","source_id":"external-1","excerpt":"exact external evidence","start_position":0,"end_position":23}]'::jsonb) from search_job;
select is((select source_url from public.citations),'https://evidence.example','external citation URL comes from stored source');
select is((select source_id from public.citations),'external-1','citation preserves external source identity');
select is((select spent_usd from public.get_usage_summary('66666666-6666-4666-8666-666666666666')),0.006::numeric,'search plan charge and actual model cost sum exactly');
reset role;
set local role authenticated;
select throws_ok($$select public.submit_search_items('66666666-6666-4666-8666-666666666666',array['https://other.example'])$$,'42501',null,'browser cannot invoke server submission');
select throws_ok($$select public.reserve_web_search('66666666-6666-4666-8666-666666666666','66666666-6666-4666-8666-666666666666','66666666-6666-4666-8666-666666666666',1)$$,'42501',null,'browser cannot reserve search charges');
reset role;
select * from finish();
rollback;
