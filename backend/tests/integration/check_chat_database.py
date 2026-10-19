"""Synthetic chat SQL/concurrency checks against an explicit disposable local database."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from check_processing_database import execute, local_environment


def main() -> int:
    environment = local_environment()
    if environment is None:
        print("UNAVAILABLE: configure the explicit disposable local PostgreSQL test database")
        return 77
    output = execute(
        (Path(__file__).resolve().parents[3] / "supabase/tests/analysis_chat.test.sql").read_text(),
        environment,
    )
    assert "not ok" not in output and "Looks like" not in output and "1.." in output
    print("PASS: analysis_chat.test.sql", output.strip().splitlines()[-1])
    owner = uuid4()
    turns = [uuid4(), uuid4(), uuid4()]
    try:
        execute(
            f"""insert into auth.users(id,email) values('{owner}','chat-concurrency@example.test');
            select public.get_or_create_account_profile(
              '{owner}','chat-concurrency@example.test',false);
            select public.submit_fetch_items('{owner}',
              array['https://chat.test/a','https://chat.test/b','https://chat.test/c']);
            update public.items set status='completed' where user_id='{owner}';
            insert into public.source_contents(
              item_id,user_id,acquisition_method,content,content_hash)
              select id,user_id,'fetch',repeat('Complete evidence. ',30),'hash'
              from public.items where user_id='{owner}';
            insert into public.assessments(
              item_id,user_id,note,criteria,score,verdict,threshold_snapshot)
              select id,user_id,'Saved analysis','[]',75,'valuable',60
              from public.items where user_id='{owner}';
            select public.set_user_budget('{owner}',1);""",
            environment,
        )
        items = (
            execute(
                f"select id from public.items where user_id='{owner}' order by original_url;",
                environment,
            )
            .strip()
            .splitlines()
        )
        for item, turn in zip(items[:2], turns[:2], strict=True):
            execute(
                f"select public.begin_chat_turn('{owner}','{item}','{turn}','Question');",
                environment,
            )

        def simultaneous(sqls: list[str]) -> list[str]:
            barrier = Barrier(2)

            def run(sql: str) -> str:
                barrier.wait(timeout=10)
                return execute(sql, environment).strip()

            with ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(run, sqls))

        admitted = simultaneous(
            [
                f"select count(*) from public.reserve_chat_call("
                f"'{owner}','{turn}','classification',0.6);"
                for turn in turns[:2]
            ]
        )
        assert sorted(admitted) == ["0", "1"]
        print("PASS: concurrent chat calls share one budget lock")
        turn = turns[admitted.index("1")]
        assert (
            execute(
                f"select count(*) from public.reserve_chat_call("
                f"'{owner}','{turn}','decision',0.1);",
                environment,
            ).strip()
            == "1"
        )
        searches = simultaneous(
            [f"select count(*) from public.reserve_chat_call('{owner}','{turn}','search',0.1);"] * 2
        )
        assert sorted(searches) == ["0", "1"]
        print("PASS: concurrent requests reserve exactly one search slot")
        execute(
            f"select public.settle_analysis('{owner}',id,0.01) from public.usage_reservations "
            f"where chat_turn_id='{turn}' and chat_slot='search'; "
            f"select public.reserve_chat_call('{owner}','{turn}','answer',0.01);",
            environment,
        )
        refinements = simultaneous(
            [
                f"select count(*) from public.reserve_chat_call("
                f"'{owner}','{turn}','search_refined',0.01);"
            ]
            * 2
        )
        assert sorted(refinements) == ["0", "1"]
        print("PASS: concurrent requests reserve exactly one refined search slot")
        finals = simultaneous(
            [
                f"select count(*) from public.reserve_chat_call("
                f"'{owner}','{turn}','answer_final',0.01);"
            ]
            * 2
        )
        assert sorted(finals) == ["0", "1"]
        print("PASS: concurrent requests reserve exactly one final answer slot")
        claimed = simultaneous(
            [
                f"select claimed from public.begin_chat_turn('{owner}',"
                f"'{items[2]}','{turns[2]}','Duplicate');"
            ]
            * 2
        )
        assert sorted(claimed) == ["f", "t"]
        print("PASS: concurrent duplicate questions claim one executor")
        classifiers = simultaneous(
            [
                f"select count(*) from public.reserve_chat_call("
                f"'{owner}','{turns[2]}','classification',0.01);"
            ]
            * 2
        )
        assert sorted(classifiers) == ["0", "1"]
        print("PASS: concurrent requests reserve exactly one classification slot")
        simultaneous(
            [
                f"select public.delete_items('{owner}',array['{items[2]}'::uuid],true);",
                f"select public.finish_chat_turn('{owner}','{turns[2]}',"
                '\'{"status":"completed","answer":[],"sources":[]}\');',
            ]
        )
        assert (
            execute(
                f"select count(*) from public.chat_turns where id='{turns[2]}';", environment
            ).strip()
            == "0"
        )
        print("PASS: concurrent deletion fences and removes chat content")
    finally:
        execute(f"delete from auth.users where id='{owner}';", environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
