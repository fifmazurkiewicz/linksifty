begin;
select plan(24);
insert into auth.users(id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at)
 values ('11111111-1111-4111-8111-111111111111','authenticated','authenticated','budget1@example.test','',now(),now(),now()),
 ('22222222-2222-4222-8222-222222222222','authenticated','authenticated','budget2@example.test','',now(),now(),now());
select public.get_or_create_account_profile('11111111-1111-4111-8111-111111111111','budget1@example.test',true);
select public.get_or_create_account_profile('22222222-2222-4222-8222-222222222222','budget2@example.test',true);
select public.get_user_settings('11111111-1111-4111-8111-111111111111');
select public.get_user_settings('22222222-2222-4222-8222-222222222222');
select is((select limit_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),10::numeric,'default cap is 10 USD');
select public.set_user_budget('11111111-1111-4111-8111-111111111111',1);
select public.update_user_threshold('11111111-1111-4111-8111-111111111111',75);
select public.submit_fetch_items('11111111-1111-4111-8111-111111111111',array['https://one.example','https://two.example']);
create temporary table first_job as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
create temporary table reserved as select r.* from first_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.60) r;
select is((select count(*)::int from reserved),1,'first reservation admitted');
select is((select threshold_snapshot from reserved),75::numeric,'threshold snapshot is atomic with reservation');
select public.update_user_threshold('11111111-1111-4111-8111-111111111111',90);
select is((select threshold_snapshot from reserved),75::numeric,'existing snapshot does not change');
create temporary table second_job as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
select is((select count(*)::int from second_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.60)),0,'second reservation cannot exceed cap');
select is((select reserved_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.60::numeric,'outstanding amount remains visible');
select public.settle_analysis(r.user_id,r.id,0.00012345) from reserved r;
select public.settle_analysis(r.user_id,r.id,0.00012345) from reserved r;
select is((select spent_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.00012345::numeric,'subcent settlement is exact and idempotent');
select is((select reserved_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0::numeric,'settled amount is no longer reserved');
select public.set_user_budget('11111111-1111-4111-8111-111111111111',0);
select is((select remaining_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0::numeric,'lowered cap preserves spending and stops availability');
select throws_ok($$select public.update_user_threshold('11111111-1111-4111-8111-111111111111',39)$$,'P0001','invalid_threshold','threshold below 40 rejected');
select is((select count(*)::int from first_job j cross join lateral public.set_processing_stage(j.user_id,j.id,'33333333-3333-4333-8333-333333333333','completed','completed')),0,'stale lease cannot publish progress');
insert into public.usage_reservations(user_id,month,amount_usd,created_at)
 values ('11111111-1111-4111-8111-111111111111',(date_trunc('month',now() at time zone 'UTC') - interval '1 month')::date,0.30,now()-interval '40 days');
select public.cleanup_processing_data('11111111-1111-4111-8111-111111111111');
select is((select reserved_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.30::numeric,'old unresolved reservation survives cleanup and month rollover');
update public.usage_reservations set created_at = now()-interval '31 days' where state='settled';
select public.cleanup_processing_data('11111111-1111-4111-8111-111111111111');
select is((select count(*)::int from public.usage_reservations where state='settled'),0,'settled detail expires after 30 days');
select is((select spent_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),0.00012345::numeric,'detail cleanup does not erase current-month total');
-- Worker liveness is separate from durable stage; stale leases cannot refresh it.
select is((select count(*)::int from first_job j cross join lateral public.heartbeat_processing_job(j.user_id,j.id,j.lease_token)),1,'valid owner can heartbeat');
select is((select worker_active from public.list_processing_items('11111111-1111-4111-8111-111111111111') where id=(select item_id from first_job)),true,'fresh heartbeat is active');
update public.jobs set heartbeat_at=now()-interval '90 seconds' where id=(select id from first_job);
-- The previous assertion confirms a running worker, this confirms interrupted UI semantics.
select is((select worker_active from public.list_processing_items('11111111-1111-4111-8111-111111111111') where id=(select item_id from first_job)),false,'stale heartbeat is not active');
select public.set_user_budget('11111111-1111-4111-8111-111111111111',1);
select public.resume_processing_item('11111111-1111-4111-8111-111111111111',item_id) from second_job;
create temporary table retry_job as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
create temporary table retry_reservation as select r.* from retry_job j cross join lateral public.reserve_analysis(j.user_id,j.id,j.lease_token,0.60) r;
select public.settle_analysis(user_id,id,1.2) from retry_reservation;
select is((select spent_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),1.20012345::numeric,'actual cost above reservation is recorded in full');
select public.settle_analysis(user_id,id,0.02) from public.usage_reservations where user_id='11111111-1111-4111-8111-111111111111' and state='reserved' and month<date_trunc('month',now() at time zone 'UTC')::date;
select is((select spent_usd from public.get_usage_summary('11111111-1111-4111-8111-111111111111')),1.20012345::numeric,'previous-month settlement does not charge current month');
-- A manually verified no-ID cost can leave cost_unknown safely, without resending inference.
select public.set_processing_stage(user_id,id,lease_token,'cost_unknown','failed') from retry_job;
update public.jobs set updated_at=now()-interval '31 seconds' where id=(select id from retry_job);
select is((select count(*)::int from public.claim_processing_job('11111111-1111-4111-8111-111111111111')),1,'settled no-ID call can be recovered without another paid attempt');
set local role authenticated;
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
select is((select count(*)::int from public.settings),1,'owner can only read own settings');
select throws_ok($$update public.settings set monthly_budget_usd=100$$,'42501',null,'direct budget writes are denied');
select throws_ok($$select public.set_user_budget('11111111-1111-4111-8111-111111111111',100)$$,'42501',null,'clients cannot invoke server budget RPC');
select is((select count(*)::int from public.usage_reservations where user_id='22222222-2222-4222-8222-222222222222'),0,'other-owner reservation reads are hidden');
reset role;
select * from finish();
rollback;
