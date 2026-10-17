begin;
select plan(30);
insert into auth.users(id,email) values
 ('11111111-1111-4111-8111-111111111111','deletion@example.test'),
 ('22222222-2222-4222-8222-222222222222','other-deletion@example.test');
select public.get_or_create_account_profile('11111111-1111-4111-8111-111111111111','deletion@example.test',false);
select public.get_or_create_account_profile('22222222-2222-4222-8222-222222222222','other-deletion@example.test',true);
select public.submit_fetch_items('11111111-1111-4111-8111-111111111111',array['https://delete.example/one','https://delete.example/two','https://delete.example/keep']);
select public.submit_fetch_items('22222222-2222-4222-8222-222222222222',array['https://foreign.example']);
create temporary table targets as select id from public.items where original_url in ('https://delete.example/one','https://delete.example/two');
update public.jobs set status='processing',lease_token=gen_random_uuid(),lease_expires_at=now()+interval '60 seconds',web_search=true
 where item_id in(select id from targets);
create temporary table active_jobs as select * from public.jobs where item_id in(select id from targets);
create temporary table reservations as select r.* from active_jobs j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.10) r;
select public.settle_analysis(user_id,id,0.02) from reservations where job_id=(select j.id from active_jobs j join public.items i on i.id=j.item_id where i.original_url='https://delete.example/one');
create temporary table search_reservation as select r.* from active_jobs j cross join lateral public.reserve_web_search(j.user_id,j.id,j.lease_token,0.03) r where j.item_id=(select id from public.items where original_url='https://delete.example/two');
update public.usage_reservations set rubric_snapshot=jsonb_set(rubric_snapshot,'{criteria,0,description}','"Private custom rule"') where id in(select id from reservations);
insert into public.source_contents(item_id,user_id,acquisition_method,content,content_hash)
 select id,user_id,'fetch',repeat('Private article. ',30),'hash' from public.items where id in(select id from targets);
insert into public.assessments(item_id,user_id,note,criteria,score,verdict,threshold_snapshot)
 select id,user_id,'Private analysis','[]'::jsonb,75,'valuable',60 from public.items where original_url='https://delete.example/one';
insert into public.citations(assessment_id,user_id,excerpt,start_position,end_position)
 select id,user_id,'Private article.',0,16 from public.assessments;
insert into public.chat_messages(item_id,user_id,role,content)
 select id,user_id,'user','Private conversation' from public.items where original_url='https://delete.example/one';

select throws_ok($$select public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from targets),false)$$,'22023','deletion_confirmation_required','explicit confirmation required');
select throws_ok($$select public.delete_items('11111111-1111-4111-8111-111111111111','{}',true)$$,'22023','invalid_deletion_selection','empty selection rejected');
select throws_ok($$select public.delete_items('11111111-1111-4111-8111-111111111111',array[null]::uuid[],true)$$,'22023','invalid_deletion_selection','null IDs rejected');
select throws_ok($$select public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from targets union all select id from targets),true)$$,'22023','invalid_deletion_selection','duplicate IDs rejected');
select throws_ok($$select public.delete_items('11111111-1111-4111-8111-111111111111',array(select gen_random_uuid() from generate_series(1,51)),true)$$,'22023','invalid_deletion_selection','oversized selection rejected');
select is((select count(*)::int from public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from public.items where original_url in ('https://delete.example/one','https://foreign.example')),true)),0,'mixed ownership rejects entire batch');
select is((select count(*)::int from public.items where id in(select id from targets)),2,'mixed batch preserves owned links');
insert into public.usage_reservations(user_id,job_id,month,amount_usd,state,generation_id)
 select '22222222-2222-4222-8222-222222222222',r.job_id,date '2026-10-01',0.01,'settled','malformed-owner'
 from reservations r join public.usage_reservations u on u.id=r.id where u.state='settled';
select is((select count(*)::int from public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from targets),true)),0,'inconsistent billing ownership blocks deletion');
select ok(exists(select 1 from public.usage_reservations where user_id='22222222-2222-4222-8222-222222222222' and generation_id='malformed-owner' and job_id is not null),'other account billing reference is untouched');
delete from public.usage_reservations where user_id='22222222-2222-4222-8222-222222222222' and generation_id='malformed-owner';
select is((select count(*)::int from public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from targets),true)),2,'confirmed batch deletes both owned links');
select is((select count(*)::int from public.source_contents),0,'source content hard deleted');
select is((select count(*)::int from public.jobs where item_id in(select id from targets)),0,'processing jobs hard deleted');
select is((select count(*)::int from public.assessments),0,'analysis hard deleted');
select is((select count(*)::int from public.citations),0,'citations hard deleted');
select is((select count(*)::int from public.chat_messages),0,'chat hard deleted');
select is((select count(*)::int from public.items where original_url='https://foreign.example'),1,'other account link preserved');
select is((select count(*)::int from public.items where original_url='https://delete.example/keep'),1,'unselected link preserved');
select is((select count(*)::int from public.usage_reservations where job_id is null),3,'model and Brave billing records survive as orphans');
select ok(not exists(select 1 from public.usage_reservations where rubric_snapshot::text like '%Private custom rule%'),'billing records retain no custom rubric text');
select is((select spent_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.02::numeric,'spent budget unchanged');
select is((select reserved_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.13::numeric,'unresolved charges remain reserved');
select is((select trial_links_used from public.account_profiles where user_id='11111111-1111-4111-8111-111111111111'),3,'trial usage not refunded');
select is((select count(*)::int from active_jobs j cross join lateral public.save_job_source(j.user_id,j.id,j.lease_token,repeat('Late source. ',30))),0,'late worker cannot recreate source');
select is((select count(*)::int from active_jobs j join reservations r on r.job_id=j.id cross join lateral public.record_model_result(j.user_id,j.id,j.lease_token,r.id,'{"note":"Late private result"}','late-generation')),0,'late result cannot recreate analysis');
select is((select count(*)::int from public.usage_reservations where generation_id='late-generation'),2,'late generation IDs remain reconcilable');
select is((select count(*)::int from active_jobs j cross join lateral public.complete_processing_job(j.user_id,j.id,j.lease_token,'{}','[]')),0,'late completion cannot recreate deleted link');
set local role authenticated;
select throws_ok($$select public.delete_items('11111111-1111-4111-8111-111111111111','{}',true)$$,'42501',null,'browser cannot invoke server-only deletion RPC');
reset role;
insert into public.source_contents(item_id,user_id,acquisition_method,content,content_hash)
 select id,'22222222-2222-4222-8222-222222222222','fetch','Malformed historical ownership','hash'
 from public.items where original_url='https://delete.example/keep';
select is((select count(*)::int from public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from public.items where original_url='https://delete.example/keep'),true)),0,'inconsistent child ownership blocks deletion');
select is((select count(*)::int from public.source_contents),1,'foreign child content is preserved');
delete from public.source_contents where content='Malformed historical ownership';
select is((select count(*)::int from public.delete_items('11111111-1111-4111-8111-111111111111',array(select id from public.items where original_url='https://delete.example/keep'),true)),1,'single link uses same deletion transaction');
select * from finish();
rollback;
