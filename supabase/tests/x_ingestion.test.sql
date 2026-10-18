begin;
select plan(10);
insert into auth.users(id,email) values
 ('11111111-1111-4111-8111-111111111111','x-owner@example.test'),
 ('22222222-2222-4222-8222-222222222222','x-other@example.test');
select public.get_or_create_account_profile('11111111-1111-4111-8111-111111111111','x-owner@example.test',true);
select public.get_or_create_account_profile('22222222-2222-4222-8222-222222222222','x-other@example.test',true);
select public.submit_fetch_items('11111111-1111-4111-8111-111111111111',array['https://x.com/user/status/100']);
create temporary table claimed as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
select is((select count(*)::int from claimed),1,'one owned job claimed');
select is((select public.begin_x_fetch('22222222-2222-4222-8222-222222222222',id,lease_token) from claimed),false,'other owner cannot admit X reads');
select is((select public.begin_x_fetch(user_id,id,gen_random_uuid()) from claimed),false,'wrong lease cannot admit X reads');
select is((select public.begin_x_fetch(user_id,id,lease_token) from claimed),true,'current owner and lease admit one attempt');
select is((select public.begin_x_fetch(user_id,id,lease_token) from claimed),false,'same lease cannot repeat attempt');
update public.jobs set lease_expires_at=now()-interval '1 second' where id in(select id from claimed);
create temporary table reclaimed as select * from public.claim_processing_job('11111111-1111-4111-8111-111111111111');
select is((select public.begin_x_fetch(user_id,id,lease_token) from reclaimed),false,'crash reclaim cannot repeat potentially billed read');
select is((select public.begin_x_fetch(user_id,id,lease_token) from claimed),false,'old lease remains fenced');
select public.submit_fetch_items('11111111-1111-4111-8111-111111111111',array['https://x.com/user/status/101']);
update public.jobs set lease_expires_at=now()-interval '1 second' where item_id in(select id from public.items where original_url='https://x.com/user/status/101');
select is((select public.begin_x_fetch(user_id,id,lease_token) from public.jobs where item_id in(select id from public.items where original_url='https://x.com/user/status/101')),false,'unclaimed job cannot start reads');
set local role authenticated;
select throws_ok($$select public.begin_x_fetch('11111111-1111-4111-8111-111111111111',gen_random_uuid(),gen_random_uuid())$$,'42501',null,'browser cannot invoke attempt RPC');
reset role;
select ok((select x_fetch_started from public.jobs where id in(select id from claimed)),'attempt survives claim recovery');
select * from finish();
rollback;
