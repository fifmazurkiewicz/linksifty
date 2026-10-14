begin;

select plan(13);

insert into auth.users (
  id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at
) values
  ('11111111-1111-4111-8111-111111111111', 'authenticated', 'authenticated',
   'pending@example.test', '', now(), now(), now()),
  ('22222222-2222-4222-8222-222222222222', 'authenticated', 'authenticated',
   'approved@example.test', '', now(), now(), now());

select public.get_or_create_account_profile(
  '11111111-1111-4111-8111-111111111111', 'pending@example.test', false
);
select public.get_or_create_account_profile(
  '22222222-2222-4222-8222-222222222222', 'approved@example.test', true
);

select is(
  (select status::text from public.account_profiles where user_id = '11111111-1111-4111-8111-111111111111'),
  'pending',
  'regular first login creates a pending account'
);
select is(
  (select status::text from public.account_profiles where user_id = '22222222-2222-4222-8222-222222222222'),
  'approved',
  'configured initial admin profile starts approved'
);
select is(
  (select count(*)::integer from public.submit_fetch_items(
    '11111111-1111-4111-8111-111111111111',
    array['https://one.example', 'https://two.example', 'https://three.example']
  )),
  3,
  'pending user can submit three trial links'
);
select throws_ok(
  $$select * from public.submit_fetch_items('11111111-1111-4111-8111-111111111111', array['https://four.example'])$$,
  'P0001',
  'account_trial_limit_exceeded',
  'pending user is stopped after three trial links'
);
select is(
  (select count(*)::integer from public.items where user_id = '11111111-1111-4111-8111-111111111111'),
  3,
  'rejected batch creates no partial items'
);
select is(
  (select trial_links_used from public.account_profiles where user_id = '11111111-1111-4111-8111-111111111111'),
  3,
  'rejected batch does not advance the trial counter'
);

select public.get_or_create_account_profile(
  '11111111-1111-4111-8111-111111111111', 'pending@example.test', false
);
select is(
  (select status::text from public.account_profiles where user_id = '11111111-1111-4111-8111-111111111111'),
  'pending',
  'repeated login does not reset a pending decision'
);
select is(
  (select trial_links_used from public.account_profiles where user_id = '11111111-1111-4111-8111-111111111111'),
  3,
  'repeated login does not reset the trial counter'
);

select * from public.set_account_profile_status(
  '11111111-1111-4111-8111-111111111111', 'rejected'
);
select throws_ok(
  $$select * from public.submit_fetch_items('11111111-1111-4111-8111-111111111111', array['https://rejected.example'])$$,
  'P0001',
  'account_rejected',
  'rejected accounts cannot submit links'
);
select is(
  (select count(*)::integer from public.items where user_id = '11111111-1111-4111-8111-111111111111'),
  3,
  'rejected account submission creates no extra rows'
);

select is(
  (select count(*)::integer from public.submit_fetch_items(
    '22222222-2222-4222-8222-222222222222',
    array['https://a.example', 'https://b.example', 'https://c.example', 'https://d.example']
  )),
  4,
  'approved admin account is not trial limited'
);

select * from public.set_account_profile_status(
  '11111111-1111-4111-8111-111111111111', 'approved'
);
select is(
  (select count(*)::integer from public.account_notifications where user_id = '11111111-1111-4111-8111-111111111111'),
  1,
  'approval transaction creates one durable notification'
);
select * from public.set_account_profile_status(
  '11111111-1111-4111-8111-111111111111', 'approved'
);
select is(
  (select count(*)::integer from public.account_notifications where user_id = '11111111-1111-4111-8111-111111111111'),
  1,
  'repeated approval does not enqueue a duplicate notification'
);

select * from finish();
rollback;
