"""Explicit local PostgreSQL gate: pgTAP plus overlapping budget reservations.

Requires a disposable, already-migrated Supabase-compatible database whose name
ends in _test, local psql and pgTAP. Never discovers credentials, installs tools,
resets a database or contacts paid providers. Exit 77 means runtime unavailable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from urllib.parse import unquote, urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]


def execute(sql: str, environment: dict[str, str]) -> str:
    result = subprocess.run(
        ["psql", "-XqAt", "-v", "ON_ERROR_STOP=1"],
        input=sql,
        text=True,
        capture_output=True,
        env=environment,
        timeout=45,
        check=False,
    )
    if result.returncode:
        # Do not print connection strings or arbitrary database/server diagnostics.
        raise RuntimeError("PostgreSQL gate failed; inspect the disposable database locally")
    return result.stdout


def local_environment() -> dict[str, str] | None:
    url = os.environ.get("LINKSIFTY_TEST_DATABASE_URL")
    if not shutil.which("psql") or not url:
        return None
    parsed = urlparse(url)
    database = unquote(parsed.path.lstrip("/"))
    if (
        parsed.scheme not in {"postgresql", "postgres"}
        or parsed.hostname
        not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }
        or not database.endswith("_test")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use an explicit loopback disposable database with an _test suffix")
    environment = {
        **{
            name: value
            for name, value in os.environ.items()
            if not name.startswith("PG") and name != "LINKSIFTY_TEST_DATABASE_URL"
        },
        "PGHOST": "127.0.0.1" if parsed.hostname == "localhost" else parsed.hostname,
        "PGPORT": str(parsed.port or 5432),
        "PGDATABASE": database,
        "PGCONNECT_TIMEOUT": "5",
    }
    if parsed.username:
        environment["PGUSER"] = unquote(parsed.username)
    if parsed.password:
        environment["PGPASSWORD"] = unquote(parsed.password)
    return environment


def concurrent_reservations(environment: dict[str, str]) -> None:
    user = str(uuid4())
    try:
        execute(
            f"""
          begin;
          insert into auth.users(id, aud, role, email, encrypted_password,
            email_confirmed_at, created_at, updated_at)
          values ('{user}', 'authenticated', 'authenticated',
            'concurrency@example.test', '', now(), now(), now());
          select public.get_or_create_account_profile('{user}', 'concurrency@example.test', true);
          select public.set_user_budget('{user}', 1);
          select public.submit_fetch_items('{user}', array['https://one.example', 'https://two.example']);
          commit;
        """,
            environment,
        )
        jobs = [
            json.loads(
                execute(
                    f"select row_to_json(j) from public.claim_processing_job('{user}') j;",
                    environment,
                ).strip()
            )
            for _ in range(2)
        ]
        barrier = Barrier(2)

        def reserve(job: dict[str, object]) -> int:
            barrier.wait(timeout=10)
            output = execute(
                f"""begin;
              select count(*) from public.reserve_analysis(
                '{user}', '{job["id"]}', '{job["lease_token"]}', 0.60);
              select pg_sleep(0.25);
              commit;""",
                environment,
            )
            return int(output.strip())

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, jobs))
        if sorted(results) != [0, 1]:
            raise AssertionError("Concurrent reservations overspent the 1 USD budget")
        summary = json.loads(
            execute(
                f"select row_to_json(u) from public.get_usage_summary('{user}') u;",
                environment,
            ).strip()
        )
        if str(summary["reserved_usd"]) not in {"0.6", "0.60"}:
            raise AssertionError("Concurrent usage summary differs from admitted work")
        print("PASS: two overlapping 0.60 USD reservations admit exactly one under a 1 USD cap")
    finally:
        # Only the random test-owned UUID in this explicitly disposable local DB.
        execute(
            f"delete from auth.users where id = '{user}' and email = 'concurrency@example.test';",
            environment,
        )


def main() -> int:
    environment = local_environment()
    if environment is None:
        print(
            "UNAVAILABLE: local psql and LINKSIFTY_TEST_DATABASE_URL are required; no checks passed"
        )
        return 77
    for name in (
        "account_approval.test.sql",
        "processing_usage.test.sql",
        "processing_recovery.test.sql",
    ):
        output = execute((ROOT / "supabase" / "tests" / name).read_text(), environment)
        if "not ok" in output or "Looks like" in output or "1.." not in output:
            raise AssertionError(f"pgTAP failed: {name}")
        print(f"PASS: {name}")
    concurrent_reservations(environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
