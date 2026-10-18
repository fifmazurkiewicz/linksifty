import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import pytest

from linksifty.application.chat_contracts import (
    ChatClaim,
    ChatContext,
    ChatDraft,
    ChatError,
    ChatModelResult,
    ChatProvider,
    ChatStore,
    ChatTurn,
    DraftParagraph,
)
from linksifty.application.chat_service import ChatService
from linksifty.application.processing_contracts import AssessmentView, EvidenceSource
from linksifty.application.research_contracts import SearchResponse
from linksifty.domain.acquisition import FetchFailure, FetchResult


def setup_chat() -> tuple[ChatService, AsyncMock, AsyncMock, AsyncMock, AsyncMock, ChatTurn]:
    store = create_autospec(ChatStore, instance=True)
    provider = create_autospec(ChatProvider, instance=True)
    fetch = AsyncMock(return_value=FetchResult(text="Independent supporting evidence. " * 30))
    search = AsyncMock()
    search.search.return_value = SearchResponse(True, ("https://source.test/article",))
    turn = ChatTurn(id=uuid4(), item_id=uuid4(), question="Explain the topic", status="pending")
    store.context.return_value = ChatContext(
        text="The saved original article explains the mechanism. " * 30,
        url="https://original.test/article",
        assessment=AssessmentView(
            note="The saved analysis",
            criteria=[],
            score=75,
            verdict="valuable",
            threshold_snapshot=60,
        ),
    )
    store.history.return_value = []
    store.claim_turn.return_value = ChatClaim(turn=turn, claimed=True)
    store.reserve_call.return_value = uuid4()
    store.finish.side_effect = lambda owner, current, **values: current.model_copy(update=values)
    provider.estimate.return_value = Decimal("0.15")
    provider.reply.return_value = ChatModelResult(
        draft=ChatDraft(
            paragraphs=[DraftParagraph(text="Grounded answer", passage_ids=["primary:1"])],
            search_query=None,
            insufficient=False,
        ),
        cost=Decimal("0.001"),
    )
    return (
        ChatService(store, provider, fetch, search=search, search_price=Decimal("0.005")),
        store,
        provider,
        fetch,
        search,
        turn,
    )


def test_saved_context_answer_does_not_search_and_restores_exact_evidence() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "completed"
        assert result.answer[0].text == "Grounded answer"
        assert result.answer[0].citations[0].excerpt in store.context.return_value.text
        assert result.answer[0].citations[0].source_url == "https://original.test/article"
        search.search.assert_not_awaited()
        fetch.assert_not_awaited()
        assert provider.reply.await_count == 1

    asyncio.run(run())


def test_research_makes_one_search_then_disables_search_and_reuses_context() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        provider.reply.side_effect = [
            ChatModelResult(
                draft=ChatDraft(
                    search_query="topic primary evidence", paragraphs=[], insufficient=False
                ),
                cost=Decimal("0.001"),
            ),
            ChatModelResult(
                draft=ChatDraft(
                    search_query=None,
                    paragraphs=[DraftParagraph(text="Further evidence", passage_ids=["chat1:1"])],
                    insufficient=False,
                ),
                cost=Decimal("0.002"),
            ),
        ]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "completed"
        assert result.search_status == "ready"
        assert result.answer[0].citations[0].source_url == "https://source.test/article"
        search.search.assert_awaited_once_with("topic primary evidence")
        assert provider.reply.await_args_list[0].kwargs["allow_search"] is True
        assert provider.reply.await_args_list[1].kwargs["allow_search"] is False
        assert store.reserve_call.await_count == 3
        fetch.assert_awaited_once()

    asyncio.run(run())


def test_duplicate_request_returns_stored_turn_without_any_paid_work() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        store.claim_turn.return_value = ChatClaim(turn=turn, claimed=False)
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.id == turn.id
        store.reserve_call.assert_not_awaited()
        provider.reply.assert_not_awaited()
        search.search.assert_not_awaited()

    asyncio.run(run())


def test_missing_or_incomplete_context_cannot_start_or_read_chat() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        store.context.return_value = None
        with pytest.raises(ChatError, match="not_found"):
            await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        with pytest.raises(ChatError, match="not_found"):
            await service.history(uuid4(), turn.item_id)
        store.claim_turn.assert_not_awaited()
        provider.reply.assert_not_awaited()

    asyncio.run(run())


def test_budget_denial_prevents_provider_call() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        store.reserve_call.return_value = None
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "failed"
        assert result.error == "budget_exhausted"
        provider.reply.assert_not_awaited()

    asyncio.run(run())


@pytest.mark.parametrize("second_query", [None, "search again"])
def test_fabricated_evidence_or_second_search_cannot_become_an_answer(
    second_query: str | None,
) -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        provider.reply.side_effect = [
            ChatModelResult(
                draft=ChatDraft(search_query="topic", paragraphs=[], insufficient=False),
                cost=Decimal("0.001"),
            ),
            ChatModelResult(
                draft=ChatDraft(
                    search_query=second_query,
                    paragraphs=[]
                    if second_query
                    else [DraftParagraph(text="Invented", passage_ids=["invented:1"])],
                    insufficient=False,
                ),
                cost=Decimal("0.001"),
            ),
        ]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "failed"
        assert not result.answer
        assert search.search.await_count == 1

    asyncio.run(run())


def test_failed_fetch_is_never_used_as_evidence_and_search_is_not_repeated() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        fetch.return_value = FetchResult(failure=FetchFailure.PARTIAL)
        provider.reply.side_effect = [
            ChatModelResult(
                draft=ChatDraft(search_query="topic", paragraphs=[], insufficient=False),
                cost=Decimal("0.001"),
            ),
            ChatModelResult(
                draft=ChatDraft(search_query=None, paragraphs=[], insufficient=True),
                cost=Decimal("0.001"),
            ),
        ]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "completed"
        assert result.insufficient is True
        assert result.search_status == "no_sources"
        assert result.sources == []
        search.search.assert_awaited_once()

    asyncio.run(run())


def test_unknown_cost_remains_reserved_and_generation_is_recorded() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        provider.reply.return_value = ChatModelResult(
            failure_reason="provider_unreachable", generation_id="gen-unknown"
        )
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "failed"
        store.record_call.assert_awaited_once()
        store.settle.assert_not_awaited()
        provider.reply.assert_awaited_once()

    asyncio.run(run())


def test_follow_up_reuses_prior_sources_and_recent_conversation_without_search() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        previous = turn.model_copy(
            update={
                "id": uuid4(),
                "question": "Earlier question",
                "status": "completed",
                "sources": [
                    EvidenceSource(
                        id="chat",
                        url="https://prior.test",
                        text="Prior fetched source evidence. " * 30,
                    )
                ],
            }
        )
        store.history.return_value = [previous]
        provider.reply.return_value = ChatModelResult(
            draft=ChatDraft(
                search_query=None,
                paragraphs=[DraftParagraph(text="Follow-up", passage_ids=["chat1:1"])],
                insufficient=False,
            ),
            cost=Decimal("0.001"),
        )
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.answer[0].citations[0].source_url == "https://prior.test"
        payload = provider.reply.await_args.args[0]
        assert payload.history[0]["content"] == "Earlier question"
        search.search.assert_not_awaited()

    asyncio.run(run())


def test_search_budget_rejection_never_calls_search_or_another_generation() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        store.reserve_call.side_effect = [uuid4(), None]
        provider.reply.return_value = ChatModelResult(
            draft=ChatDraft(search_query="topic evidence", paragraphs=[], insufficient=False),
            cost=Decimal("0.001"),
        )
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "completed" and result.insufficient
        assert result.search_status == "budget_exhausted"
        search.search.assert_not_awaited()
        assert provider.reply.await_count == 1

    asyncio.run(run())


def test_relevant_passage_near_end_of_long_article_is_available_to_chat() -> None:
    from linksifty.application.chat_service import _input

    service, store, provider, fetch, search, turn = setup_chat()
    context = store.context.return_value.model_copy(
        update={
            "text": "Unrelated introductory material. " * 1500
            + "Anisotropy mechanism explains direction-dependent propagation." * 10,
        }
    )
    payload = _input(context, [], "Explain anisotropy and propagation")
    primary = [c for key, c in payload.passages.items() if key.startswith("primary:")]
    assert any("Anisotropy mechanism" in c.excerpt for c in primary)
    assert all(c.excerpt in context.text for c in primary)
