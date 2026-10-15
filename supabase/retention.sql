-- Run once in Supabase SQL Editor after migration 20261015_000005.
-- Database scheduling is required for retention while no one visits the app.
create extension if not exists pg_cron with schema pg_catalog;
select cron.schedule(
  'linksifty-retention',
  '0 * * * *',
  'select public.cleanup_processing_data(user_id) from public.account_profiles'
);
-- Verify: select jobname, schedule, active from cron.job where jobname = 'linksifty-retention';
-- This purges expired content and settled detail (>30 days), preserves the current
-- UTC-month total and unresolved reservations, and never calls a paid provider.
