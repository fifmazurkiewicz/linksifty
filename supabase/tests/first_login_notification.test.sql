begin;
select plan(8);
insert into auth.users(id,email) values
 ('77777777-7777-4777-8777-777777777777','new@example.test'),
 ('88888888-8888-4888-8888-888888888888','owner@example.test');
select public.get_or_create_account_profile('77777777-7777-4777-8777-777777777777','new@example.test',false);
select is((select count(*)::int from public.account_notifications where user_id='77777777-7777-4777-8777-777777777777' and kind='account_requested'),1,'first login enqueues exactly one request');
select public.get_or_create_account_profile('77777777-7777-4777-8777-777777777777','new@example.test',false);
select is((select count(*)::int from public.account_notifications where user_id='77777777-7777-4777-8777-777777777777'),1,'repeat login never duplicates request');
select public.get_or_create_account_profile('88888888-8888-4888-8888-888888888888','owner@example.test',true);
select is((select count(*)::int from public.account_notifications where user_id='88888888-8888-4888-8888-888888888888'),0,'administrator creates no request');
select is((select count(*)::int from public.claim_account_notification((select id from public.account_notifications where user_id='77777777-7777-4777-8777-777777777777'))),1,'first claim owns delivery');
select is((select count(*)::int from public.claim_account_notification((select id from public.account_notifications where user_id='77777777-7777-4777-8777-777777777777'))),0,'overlapping delivery cannot claim same event');
select * from public.set_account_profile_status('77777777-7777-4777-8777-777777777777','approved');
select is((select count(*)::int from public.account_notifications where user_id='77777777-7777-4777-8777-777777777777'),1,'approval creates no second email');
select is((select status::text from public.account_profiles where user_id='77777777-7777-4777-8777-777777777777'),'approved','approval grants access');
update public.account_profiles set trial_links_used=3 where user_id='77777777-7777-4777-8777-777777777777';
select is((select count(*)::int from public.submit_fetch_items('77777777-7777-4777-8777-777777777777',array['https://a.example','https://b.example','https://c.example','https://d.example'])),4,'approved regular user can exceed exhausted trial allowance');
select * from finish();
rollback;
