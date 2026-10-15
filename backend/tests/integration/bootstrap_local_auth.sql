-- TEST ONLY: minimal Supabase auth contract for a fresh disposable PostgreSQL.
-- Not a GoTrue/JWT/hosted Supabase test; never apply to an existing environment.
do $$
begin
  if current_database() not like '%\_test' escape '\' then
    raise exception 'Disposable database name must end in _test';
  end if;
  if exists (select 1 from pg_namespace where nspname = 'auth') then
    raise exception 'Fresh database required; auth schema already exists';
  end if;
end;
$$;
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create schema auth;
create table auth.users (
  id uuid primary key,
  aud text,
  role text,
  email text,
  encrypted_password text,
  email_confirmed_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz
);
create function auth.uid() returns uuid language sql stable as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'
  )::uuid;
$$;
grant usage on schema auth, public to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
-- Mirror Supabase's initial table grants, before migrations revoke client writes.
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
-- Match hosted Supabase: pgcrypto is outside the RPC public search_path.
create schema extensions;
create extension pgcrypto with schema extensions;
create extension pgtap;
