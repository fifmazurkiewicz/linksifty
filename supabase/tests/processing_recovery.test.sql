begin;
select plan(20);
insert into auth.users(id,email) values
 ('11111111-1111-4111-8111-111111111111','recovery1@example.test'),
 ('22222222-2222-4222-8222-222222222222','recovery2@example.test');
select public.get_or_create_account_profile('11111111-1111-4111-8111-111111111111','recovery1@example.test',true);
select public.get_or_create_account_profile('22222222-2222-4222-8222-222222222222','recovery2@example.test',true);
set local role service_role;
select public.get_user_settings('11111111-1111-4111-8111-111111111111');
select public.get_user_settings('22222222-2222-4222-8222-222222222222');
select public.paste_item_content('11111111-1111-4111-8111-111111111111',repeat('source ',40));
create temporary table claimed as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
create temporary table old_reservation as select r.* from claimed j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.10) r;
select is((select count(*)::int from old_reservation),1,'service role can reserve a pasted item');
select is((select count(*)::int from claimed j cross join lateral public.save_job_source('22222222-2222-4222-8222-222222222222',j.id,j.lease_token,repeat('foreign ',40))),0,'source RPC cannot cross owner boundary');
select is((select count(*)::int from claimed j cross join lateral public.heartbeat_processing_job('22222222-2222-4222-8222-222222222222',j.id,j.lease_token)),0,'foreign owner cannot heartbeat');
select is((select count(*)::int from old_reservation r cross join lateral public.settle_analysis('22222222-2222-4222-8222-222222222222',r.id,0.01)),0,'foreign owner cannot settle reservation');
select public.settle_analysis(user_id,id,0.01) from old_reservation;
select public.set_processing_stage(user_id,id,lease_token,'invalid_model_output','failed') from claimed;
select public.resume_processing_item(user_id,item_id) from claimed;
create temporary table reclaimed as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
create temporary table new_reservation as select r.* from reclaimed j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.10) r;
select isnt((select id from new_reservation),(select id from old_reservation),'explicit safe retry creates a new reservation');
select is((select count(*)::int from claimed j cross join old_reservation r cross join lateral public.record_model_result(j.user_id,j.id,j.lease_token,r.id,'{"cost":"0.01"}'::jsonb,'old-generation')),0,'late result from old lease cannot overwrite job');
select is((select generation_id from public.usage_reservations where id=(select id from old_reservation)),'old-generation','late generation remains bound to original reservation');
select is((select generation_id from public.usage_reservations where id=(select id from new_reservation)),null::text,'late generation does not contaminate new reservation');
select is((select count(*)::int from reclaimed j cross join lateral public.complete_processing_job(j.user_id,j.id,j.lease_token,'{}'::jsonb,'[]'::jsonb)),0,'unsettled reservation cannot publish an assessment');
select public.record_model_result(j.user_id,j.id,j.lease_token,r.id,'{"cost":"0.02"}'::jsonb,'new-generation') from reclaimed j cross join new_reservation r;
select public.settle_analysis(user_id,id,0.02) from new_reservation;
select is((select count(*)::int from reclaimed j cross join lateral public.complete_processing_job(j.user_id,j.id,j.lease_token,
 '{"note":"Saved source assessment","criteria":[],"score":75,"verdict":"valuable"}'::jsonb,
 '[{"id":"33333333-3333-4333-8333-333333333333","excerpt":"source","start_position":0,"end_position":6}]'::jsonb)),1,'settled owner job publishes saved assessment');
select is((select status::text from public.items where id=(select item_id from claimed)),'completed','item reaches completed state');
select is((select model_result from public.jobs where id=(select id from claimed)),null::jsonb,'completed job discards transient model result');
select is((select spent_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.03::numeric,'both actual attempts are accounted exactly once');
select public.paste_item_content('22222222-2222-4222-8222-222222222222',repeat('private ',40));
create temporary table foreign_job as select * from public.claim_processing_job('22222222-2222-4222-8222-222222222222');
create temporary table foreign_reservation as select r.* from foreign_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.20) r;
-- Seed actual foreign rows before testing RLS; empty tables would give false confidence.
select is((select count(*)::int from public.usage_reservations where user_id='22222222-2222-4222-8222-222222222222'),1,'foreign reservation exists for RLS test');
reset role;
update public.jobs set lease_expires_at=now()-interval '1 second' where id=(select id from foreign_job);
select is((select count(*)::int from foreign_job j cross join lateral public.heartbeat_processing_job(j.user_id,j.id,j.lease_token)),0,'expired lease cannot revive itself');
select is((select count(*)::int from foreign_job j cross join lateral public.set_processing_stage(j.user_id,j.id,j.lease_token,'analyzing')),0,'expired lease cannot publish a stage');
-- Expired content removes jobs, but unresolved costs and late generation metadata survive.
update public.items set expires_at=now()-interval '1 second' where id=(select item_id from foreign_job);
select public.cleanup_processing_data('22222222-2222-4222-8222-222222222222');
select public.record_model_result(j.user_id,j.id,j.lease_token,r.id,'{}'::jsonb,'orphan-generation') from foreign_job j cross join foreign_reservation r;
select is((select generation_id from public.usage_reservations where id=(select id from foreign_reservation)),'orphan-generation','deleted job still permits original late generation reconciliation');
select is((select reserved_usd from public.get_usage_summary('22222222-2222-4222-8222-222222222222')),0.20::numeric,'expired content does not erase uncertain charge');
set local role authenticated;
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
select is((select count(*)::int from public.usage_reservations where user_id='22222222-2222-4222-8222-222222222222'),0,'RLS hides the seeded foreign reservation');
select throws_ok($$select * from public.list_processing_items('22222222-2222-4222-8222-222222222222')$$,'42501',null,'client cannot invoke owner-parameterized server content RPC');
reset role;
select * from finish();
rollback;
