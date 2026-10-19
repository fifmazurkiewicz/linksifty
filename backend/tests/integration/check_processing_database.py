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
from decimal import Decimal
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


def concurrent_duplicate_submissions(environment: dict[str, str]) -> None:
    user = str(uuid4())
    try:
        execute(
            f"""insert into auth.users(id,email) values
                  ('{user}','duplicate-race@example.test');
                  select public.get_or_create_account_profile(
                    '{user}','duplicate-race@example.test',true);""",
            environment,
        )
        barrier = Barrier(2)

        def submit(fragment: int) -> int:
            barrier.wait(timeout=10)
            try:
                output = execute(
                    f"""begin; select count(*) from public.submit_fetch_items('{user}',
                     array['https://duplicate-race.example/article#{fragment}']);
                     select pg_sleep(0.25); commit;""",
                    environment,
                )
                return int(output.strip())
            except RuntimeError:
                return 0  # pgTAP separately proves the exact duplicate SQLSTATE/message.

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, [1, 2]))
        if sorted(results) != [0, 1]:
            raise AssertionError("Concurrent duplicate submissions did not admit exactly one")
        count = (
            execute(
                f"""select count(*) from public.items where user_id='{user}';
                   select count(*) from public.jobs where user_id='{user}';""",
                environment,
            )
            .strip()
            .splitlines()
        )
        if count != ["1", "1"]:
            raise AssertionError("Duplicate race created extra item/job")
        print("PASS: concurrent fragment-equivalent URLs create exactly one item/job")
    finally:
        execute(
            f"delete from auth.users where id='{user}' and email='duplicate-race@example.test'",
            environment,
        )


def concurrent_rubric_snapshot(environment: dict[str, str]) -> None:
    """A settings update cannot split the threshold/rubric reservation snapshot."""
    from linksifty.application.processing_contracts import RubricConfig

    user = str(uuid4())
    rules = RubricConfig.default().model_dump(mode="json")
    rules["criteria"][0]["weight"] = 10
    literal = json.dumps(rules).replace("'", "''")
    try:
        execute(
            f"""insert into auth.users(id,email) values ('{user}','rubric-race@example.test');
            select public.get_or_create_account_profile('{user}','rubric-race@example.test',true);
            select public.get_user_settings('{user}');
            select public.submit_fetch_items('{user}',array['https://rubric-race.example']);""",
            environment,
        )
        job = json.loads(
            execute(
                f"select row_to_json(j) from public.claim_processing_job('{user}') j;", environment
            )
        )
        barrier = Barrier(2)

        def update() -> None:
            barrier.wait(timeout=10)
            execute(
                f"select public.update_user_assessment_settings('{user}',75,'{literal}'::jsonb);",
                environment,
            )

        def reserve() -> dict[str, object]:
            barrier.wait(timeout=10)
            return dict(
                json.loads(
                    execute(
                        f"select row_to_json(r) from public.reserve_analysis('{user}',"
                        f"'{job['id']}','{job['lease_token']}',0.01) r;",
                        environment,
                    )
                )
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            updating = pool.submit(update)
            reserving = pool.submit(reserve)
            updating.result()
            reservation = reserving.result()
        snapshot = reservation["rubric_snapshot"]
        assert isinstance(snapshot, dict)
        pair = (
            int(Decimal(str(reservation["threshold_snapshot"]))),
            snapshot["criteria"][0]["weight"],
        )
        if pair not in {(60, 1), (75, 10)}:
            raise AssertionError(
                "Reservation mixed threshold/rubric from different settings versions"
            )
        print(
            "PASS: concurrent settings update/model reservation "
            "captures one consistent rubric/threshold"
        )
    finally:
        execute(
            f"delete from auth.users where id='{user}' and email='rubric-race@example.test';",
            environment,
        )


def concurrent_deletion(environment: dict[str, str]) -> None:
    """Race deletion against admission and a late result on separate connections."""
    for operation in ("reserve", "result"):
        user = str(uuid4())
        try:
            execute(
                f"""
                insert into auth.users(id,email) values ('{user}','deletion-race@example.test');
                select public.get_or_create_account_profile(
                  '{user}','deletion-race@example.test',true);
                select public.submit_fetch_items('{user}',array['https://deletion-race.example']);
                """,
                environment,
            )
            job = json.loads(
                execute(
                    f"select row_to_json(j) from public.claim_processing_job('{user}') j;",
                    environment,
                ).strip()
            )
            if operation == "result":
                reservation = execute(
                    f"select id from public.reserve_analysis('{user}',"
                    f"'{job['id']}','{job['lease_token']}',0.20);",
                    environment,
                ).strip()
                writer_sql = (
                    f"select count(*) from public.record_model_result('{user}',"
                    f"'{job['id']}','{job['lease_token']}','{reservation}',"
                    "'{\"note\":\"Private late output\"}', 'deletion-race');"
                )
            else:
                writer_sql = (
                    f"select count(*) from public.reserve_analysis('{user}',"
                    f"'{job['id']}','{job['lease_token']}',0.20);"
                )
            barrier = Barrier(2)

            def run(sql: str, start: Barrier = barrier) -> str:
                start.wait(timeout=10)
                return execute(f"begin; {sql} select pg_sleep(0.05); commit;", environment)

            with ThreadPoolExecutor(max_workers=2) as pool:
                deletion = pool.submit(
                    run,
                    f"select count(*) from public.delete_items('{user}',"
                    f"array['{job['item_id']}']::uuid[],true);",
                )
                writer = pool.submit(run, writer_sql)
                assert deletion.result().strip() == "1"
                assert writer.result().strip() in {"0", "1"}
            state = json.loads(
                execute(
                    f"""select json_build_object(
                    'items',(select count(*) from public.items where user_id='{user}'),
                    'jobs',(select count(*) from public.jobs where user_id='{user}'),
                    'attached',(select count(*) from public.usage_reservations
                      where user_id='{user}' and job_id is not null),
                    'generations',(select count(*) from public.usage_reservations
                      where user_id='{user}' and generation_id='deletion-race'));
                    """,
                    environment,
                ).strip()
            )
            assert state["items"] == state["jobs"] == state["attached"] == 0
            if operation == "result":
                assert state["generations"] == 1
            print(f"PASS: concurrent deletion/{operation}")
        finally:
            execute(f"delete from auth.users where id='{user}';", environment)


def concurrent_x_admission(environment: dict[str, str]) -> None:
    """Only one connection may admit potentially billed reads for a job."""
    user = str(uuid4())
    try:
        execute(
            f"""
            insert into auth.users(id,email) values ('{user}','x-race@example.test');
            select public.get_or_create_account_profile('{user}','x-race@example.test',true);
            select public.submit_fetch_items('{user}',array['https://x.com/user/status/100']);
            """,
            environment,
        )
        job = json.loads(
            execute(
                f"select row_to_json(j) from public.claim_processing_job('{user}') j;",
                environment,
            ).strip()
        )
        barrier = Barrier(2)

        def admit() -> str:
            barrier.wait(timeout=10)
            return execute(
                f"select admitted from public.begin_x_fetch('{user}',"
                f"'{job['id']}','{job['lease_token']}');",
                environment,
            ).strip()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(admit), pool.submit(admit)
            assert sorted([first.result(), second.result()]) == ["f", "t"]
        print("PASS: concurrent X reads admit exactly one attempt")
    finally:
        execute(f"delete from auth.users where id='{user}';", environment)


def concurrent_image_reading(environment: dict[str, str]) -> None:
    """Distinct and duplicate image slots share the serialized budget gate."""
    for same_job in (False, True):
        _concurrent_image_case(environment, same_job)


def _concurrent_image_case(environment: dict[str, str], same_job: bool) -> None:
    user = str(uuid4())
    try:
        execute(
            f"""
            insert into auth.users(id,email) values ('{user}','image-race@example.test');
            select public.get_or_create_account_profile(
                    '{user}','image-race@example.test',true);
            select public.set_user_budget('{user}',0.2);
            select public.submit_fetch_items('{user}',array['https://x.com/user/status/100','https://x.com/user/status/200']);
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
        for job in jobs:
            execute(
                f"select public.begin_x_fetch('{user}','{job['id']}','{job['lease_token']}');",
                environment,
            )
        barrier = Barrier(2)

        def reserve(index: int) -> str:
            job = jobs[0 if same_job else index]
            barrier.wait(timeout=10)
            return execute(
                f"select id from public.reserve_image_reading('{user}',"
                f"'{job['id']}','{job['lease_token']}',0.16896);",
                environment,
            ).strip()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(reserve, 0), pool.submit(reserve, 1)
            assert sum(bool(value) for value in (first.result(), second.result())) == 1
        held = Decimal(
            execute(
                f"select reserved_usd from public.get_usage_summary('{user}');", environment
            ).strip()
        )
        assert held == Decimal("0.16896")
        print(f"PASS: concurrent image {'duplicate admission' if same_job else 'monthly budget'}")
    finally:
        execute(f"delete from auth.users where id='{user}';", environment)


def concurrent_source_selection(environment: dict[str, str], same_job: bool = False) -> None:
    user = str(uuid4())
    try:
        execute(
            f"""insert into auth.users(id,email)
                values ('{user}','selection-race@example.test');
                select public.get_or_create_account_profile(
                    '{user}','selection-race@example.test',true);
                select public.set_user_budget('{user}',{0.1 if same_job else 0.04});
                select public.submit_search_items('{user}',
                    array['https://selection-one.example','https://selection-two.example']);""",
            environment,
        )
        jobs = [
            json.loads(
                execute(
                    f"select row_to_json(j) from public.claim_processing_job('{user}') j;",
                    environment,
                )
            )
            for _ in range(2)
        ]
        for job in jobs:
            execute(
                f"""select public.save_job_source('{user}',
                    '{job["id"]}','{job["lease_token"]}',repeat('Evidence ',40));
                    select public.settle_analysis('{user}',id,0.001)
                    from public.reserve_web_search('{user}',
                        '{job["id"]}','{job["lease_token"]}',0.001);""",
                environment,
            )
        barrier = Barrier(2)

        def reserve(index: int) -> str:
            job = jobs[0 if same_job else index]
            barrier.wait(timeout=10)
            return execute(
                f"""begin; select id from public.reserve_source_selection('{user}',
                    '{job["id"]}','{job["lease_token"]}',0.02688);
                    select pg_sleep(0.25); commit;""",
                environment,
            ).strip()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(reserve, 0), pool.submit(reserve, 1)
            assert sum(bool(value) for value in (first.result(), second.result())) == 1
        held = Decimal(
            execute(
                f"select reserved_usd from public.get_usage_summary('{user}');",
                environment,
            ).strip()
        )
        assert held == Decimal("0.02688")
        label = "same-job admission" if same_job else "shared monthly budget"
        print(f"PASS: concurrent source selection {label}")
    finally:
        execute(f"delete from auth.users where id='{user}';", environment)


def concurrent_discussions(environment: dict[str, str]) -> None:
    user = str(uuid4())
    try:
        execute(
            f"""insert into auth.users(id,email) values ('{user}','discussion-race@example.test');
            select public.get_or_create_account_profile(
              '{user}','discussion-race@example.test',true);
            select public.submit_fetch_items('{user}',array['https://x.com/author/status/100']);
            update public.items set status='completed' where user_id='{user}';""",
            environment,
        )
        item = execute(f"select id from public.items where user_id='{user}';", environment).strip()
        barrier = Barrier(2)

        def admit() -> str:
            barrier.wait(timeout=10)
            return execute(
                f"select admitted from public.begin_item_discussion('{user}','{item}','primary');",
                environment,
            ).strip()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(admit) for _ in range(2)]
            outcomes = sorted(future.result(timeout=20) for future in futures)
        assert outcomes == ["f", "t"]
        print("PASS: concurrent discussion clicks admit exactly one X request")
    finally:
        execute(f"delete from auth.users where id='{user}';", environment)


def title_concurrency(environment: dict[str, str]) -> None:
    user = str(uuid4())
    try:
        execute(
            f"""insert into auth.users(id,email) values ('{user}','title-race@example.test');
            select public.get_or_create_account_profile('{user}','title-race@example.test',true);
            select public.paste_item_content('{user}',repeat('Complete source text. ',30));
            select public.paste_item_content('{user}',repeat('Another complete source. ',30));
            update public.items set status='completed' where user_id='{user}';""",
            environment,
        )
        items = execute(
            f"select id from public.items where user_id='{user}' order by id;", environment
        ).splitlines()
        for same_item in (True, False):
            execute(
                f"select public.set_user_budget('{user}',{10 if same_item else 1});", environment
            )
            barrier = Barrier(2)

            def admit(item_id: str, gate: Barrier = barrier) -> str:
                gate.wait(timeout=10)
                return execute(
                    f"select count(*) from public.reserve_item_title('{user}','{item_id}',0.6);",
                    environment,
                ).strip()

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(admit, items[0]),
                    pool.submit(admit, items[0 if same_item else 1]),
                ]
                outcomes = sorted(future.result(timeout=20) for future in futures)
            assert outcomes == ["0", "1"]
            execute(
                f"select public.settle_analysis('{user}',id,0) from public.usage_reservations "
                f"where user_id='{user}' and state='reserved';",
                environment,
            )
            print(
                "PASS: concurrent title "
                + ("duplicate admission" if same_item else "monthly budget")
            )
    finally:
        execute(f"delete from auth.users where id='{user}';", environment)


def main() -> int:
    environment = local_environment()
    if environment is None:
        print(
            "UNAVAILABLE: local psql and LINKSIFTY_TEST_DATABASE_URL are required; no checks passed"
        )
        return 77
    title_concurrency(environment)
    for name in (
        "account_approval.test.sql",
        "processing_usage.test.sql",
        "processing_recovery.test.sql",
        "processing_hash.test.sql",
        "brave_research.test.sql",
        "duplicate_links.test.sql",
        "assessment_rubric.test.sql",
        "assessment_calibration.test.sql",
        "delete_items.test.sql",
        "analysis_chat.test.sql",
        "x_ingestion.test.sql",
        "retry_fetch.test.sql",
        "image_reading.test.sql",
        "source_selection.test.sql",
        "reader_discussions.test.sql",
        "text_only_sources.test.sql",
        "ai_titles.test.sql",
    ):
        output = execute((ROOT / "supabase" / "tests" / name).read_text(), environment)
        if "not ok" in output or "Looks like" in output or "1.." not in output:
            raise AssertionError(f"pgTAP failed: {name}")
        print(f"PASS: {name}")
    concurrent_reservations(environment)
    concurrent_duplicate_submissions(environment)
    concurrent_rubric_snapshot(environment)
    concurrent_deletion(environment)
    concurrent_x_admission(environment)
    concurrent_image_reading(environment)
    concurrent_source_selection(environment, same_job=True)
    concurrent_source_selection(environment)
    concurrent_discussions(environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
