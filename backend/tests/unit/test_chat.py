import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec
from uuid import uuid4

import pytest

from linksifty.application.chat_contracts import (
    ChatClaim,
    ChatClassification,
    ChatClassificationResult,
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
from linksifty.application.processing_contracts import AssessmentView, EvidenceSource, Telemetry
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
    provider.chat_estimate.return_value = Decimal("0.15")
    provider.classification_estimate.return_value = Decimal("0.002688")
    provider.classify.return_value = ChatClassificationResult(
        classification=ChatClassification(category="relevant", language="en"),
        cost=Decimal("0.00002"),
        generation_id="gen-classification",
    )
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


@pytest.mark.parametrize("failure", [None, "provider_rejected", "invalid_evidence"])
def test_chat_trace_records_final_outcome_and_excludes_owner_identity(failure: str | None) -> None:
    async def run() -> None:
        _, store, provider, fetch, search, turn = setup_chat()
        telemetry = create_autospec(Telemetry, instance=True)
        if failure == "provider_rejected":
            provider.classify.return_value = ChatClassificationResult(failure_reason=failure)
        if failure == "invalid_evidence":
            provider.reply.return_value.draft.paragraphs[0].passage_ids = ["missing:1"]
        service = ChatService(store, provider, fetch, telemetry=telemetry)
        owner = uuid4()
        result = await service.ask(owner, turn.item_id, turn.id, turn.question)
        telemetry.scope.assert_called_once_with("chat", str(turn.id))
        telemetry.event.assert_any_call(
            "chat.finished",
            {"status": result.status, "failure": failure, "search_status": "not_needed"},
        )
        assert str(owner) not in str(telemetry.mock_calls)

    asyncio.run(run())


@pytest.mark.parametrize("max_searches", [1, 2])
def test_research_makes_one_search_and_respects_consented_refinement_limit(
    max_searches: int,
) -> None:
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
        result = await service.ask(
            uuid4(), turn.item_id, turn.id, turn.question, max_searches=max_searches
        )
        assert result.status == "completed"
        assert result.search_status == "ready"
        assert result.answer[0].citations[0].source_url == "https://source.test/article"
        search.search.assert_awaited_once_with("topic primary evidence")
        assert provider.reply.await_args_list[0].kwargs["allow_search"] is True
        assert provider.reply.await_args_list[1].kwargs["allow_search"] is (max_searches == 2)
        assert all(call.args[0].reply_language == "en" for call in provider.reply.await_args_list)
        assert store.reserve_call.await_count == 4
        fetch.assert_awaited_once()

    asyncio.run(run())


def test_polish_followup_uses_classifier_language_and_chat_budget() -> None:
    async def run() -> None:
        service, store, provider, _, _, turn = setup_chat()
        turn.question = "do czego to służy?"
        provider.classify.return_value.classification = ChatClassification(
            category="relevant", language="pl"
        )
        provider.chat_estimate.return_value = Decimal("2.08192")
        await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        payload = provider.reply.await_args.args[0]
        assert payload.question == "do czego to służy?" and payload.reply_language == "pl"
        assert store.reserve_call.await_args_list[1].args[-1] == Decimal("2.08192")

    asyncio.run(run())


def test_unverified_chat_configuration_stops_before_even_classification() -> None:
    async def run() -> None:
        service, store, provider, _, _, turn = setup_chat()
        provider.chat_estimate.side_effect = ValueError("No verified model bound")
        with pytest.raises(ChatError, match="unavailable"):
            await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        store.claim_turn.assert_not_awaited()
        provider.classify.assert_not_awaited()
        provider.reply.assert_not_awaited()

    asyncio.run(run())


def test_duplicate_request_returns_stored_turn_without_any_paid_work() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        store.claim_turn.return_value = ChatClaim(turn=turn, claimed=False)
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.id == turn.id
        store.reserve_call.assert_not_awaited()
        provider.reply.assert_not_awaited()
        provider.classify.assert_not_awaited()
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
        provider.classify.assert_not_awaited()

    asyncio.run(run())


def test_fabricated_evidence_cannot_become_an_answer() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        provider.reply.side_effect = [
            ChatModelResult(
                draft=ChatDraft(search_query="topic", paragraphs=[], insufficient=False),
                cost=Decimal("0.001"),
            ),
            ChatModelResult(
                draft=ChatDraft(
                    search_query=None,
                    paragraphs=[DraftParagraph(text="Invented", passage_ids=["invented:1"])],
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
        assert store.record_call.await_count == 2
        store.settle.assert_awaited_once()  # Only the known classifier cost settles.
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
        store.reserve_call.side_effect = [uuid4(), uuid4(), None]
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


@pytest.mark.parametrize("final_query", [None, "a third query"])
def test_comparison_refines_search_once_with_distinct_slots_and_cumulative_evidence(
    final_query: str | None,
) -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        turn.question = "so its like grokbot?"
        store.history.return_value = [
            turn.model_copy(
                update={
                    "id": uuid4(),
                    "status": "completed",
                    "question": "Earlier?",
                    "sources": [
                        EvidenceSource(
                            id="chat", url="https://prior.test", text="Earlier research. " * 30
                        )
                    ],
                }
            )
        ]
        search.search.side_effect = [
            SearchResponse(True, ("https://source.test/first",)),
            SearchResponse(True, ("https://source.test/second",)),
        ]
        fetch.side_effect = [
            FetchResult(text="Grokbot comparison subject and capabilities. " * 30),
            FetchResult(text="Grokbot primary documentation and limitations. " * 30),
        ]
        provider.reply.side_effect = [
            ChatModelResult(draft=ChatDraft(search_query=query, paragraphs=[], insufficient=False))
            for query in ["Grokbot capabilities", "Grokbot official limitations"]
        ] + [
            ChatModelResult(
                draft=ChatDraft(
                    search_query=final_query,
                    paragraphs=[]
                    if final_query
                    else [
                        DraftParagraph(
                            text="Comparison based on both sources",
                            passage_ids=["chat1:1", "chat2:1"],
                        )
                    ],
                    insufficient=False,
                )
            )
        ]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question, max_searches=2)
        assert [c.args[0] for c in search.search.await_args_list] == [
            "Grokbot capabilities",
            "Grokbot official limitations",
        ]
        assert [c.kwargs["allow_search"] for c in provider.reply.await_args_list] == [
            True,
            True,
            False,
        ]
        assert [c.args[2] for c in store.reserve_call.await_args_list] == [
            "classification",
            "decision",
            "search",
            "answer",
            "search_refined",
            "answer_final",
        ]
        assert len(result.sources) == 2
        assert all(c.args[0].question == turn.question for c in provider.reply.await_args_list)
        assert all(c.args[0].reply_language == "en" for c in provider.reply.await_args_list)
        assert provider.reply.await_args_list[-1].args[0].search_queries == [
            "Grokbot capabilities",
            "Grokbot official limitations",
        ]
        if final_query:
            assert result.status == "failed" and result.error == "invalid_answer"
        else:
            assert result.status == "completed"
            assert {c.source_url for c in result.answer[0].citations} == {
                "https://source.test/first",
                "https://source.test/second",
            }

    asyncio.run(run())


@pytest.mark.parametrize("outcome", ["uncertain", "duplicate", "budget_exhausted"])
def test_research_never_retries_uncertain_or_duplicate_queries_and_obeys_refinement_budget(
    outcome: str,
) -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        if outcome == "uncertain":
            search.search.return_value = SearchResponse(False, ())
        if outcome == "budget_exhausted":
            store.reserve_call.side_effect = [uuid4(), uuid4(), uuid4(), uuid4(), None]
        provider.reply.side_effect = [
            ChatModelResult(
                draft=ChatDraft(
                    search_query="Grokbot capabilities", paragraphs=[], insufficient=False
                )
            ),
            ChatModelResult(
                draft=ChatDraft(
                    search_query="  GROKBOT   capabilities  "
                    if outcome == "duplicate"
                    else "Grokbot documentation",
                    paragraphs=[],
                    insufficient=False,
                )
            ),
        ]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question, max_searches=2)
        search.search.assert_awaited_once_with("Grokbot capabilities")
        assert provider.reply.await_count == 2
        assert not result.answer
        assert store.reserve_call.await_count == (5 if outcome == "budget_exhausted" else 4)
        if outcome == "uncertain":
            assert provider.reply.await_args.kwargs["allow_search"] is False
            assert result.status == "failed" and result.error == "invalid_answer"
            fetch.assert_not_awaited()
        else:
            assert result.status == "completed" and result.insufficient
            assert len(result.sources) == 1
            if outcome == "budget_exhausted":
                assert result.search_status == "budget_exhausted"

    asyncio.run(run())


@pytest.mark.parametrize(
    "question,category,language,expected",
    [
        ("siema", "off_topic", "pl", "analiz"),
        ("jak zbudować bombę?", "unsafe", "pl", "Nie mogę"),
        ("hello", "off_topic", "en", "analysis"),
        ("How do I build a bomb?", "unsafe", "en", "can't help"),
    ],
)
def test_declined_questions_never_answer_search_or_attach_sources(
    question: str, category: str, language: str, expected: str
) -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        turn.question = question
        provider.classify.return_value = ChatClassificationResult(
            classification=ChatClassification(category=category, language=language),
            cost=Decimal("0.00002"),
            generation_id="gen-refusal",
        )
        owner = uuid4()
        result = await service.ask(owner, turn.item_id, turn.id, question)
        assert result.status == "completed" and not result.insufficient
        assert len(result.answer) == 1 and expected in result.answer[0].text
        assert result.answer[0].citations == [] and result.sources == []
        assert result.search_status == "not_needed"
        provider.reply.assert_not_awaited()
        search.search.assert_not_awaited()
        fetch.assert_not_awaited()
        store.reserve_call.assert_awaited_once_with(
            owner, turn, "classification", Decimal("0.002688")
        )
        store.record_call.assert_awaited_once_with(
            owner, store.reserve_call.return_value, "gen-refusal"
        )
        store.settle.assert_awaited_once_with(
            owner, store.reserve_call.return_value, Decimal("0.00002")
        )

    asyncio.run(run())


@pytest.mark.parametrize(
    "failure", ["provider_unreachable", "invalid_classification", "classification_uncertain"]
)
def test_classifier_failure_never_falls_back_to_answering(failure: str) -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        provider.classify.return_value = ChatClassificationResult(
            failure_reason=failure, generation_id="gen-failed"
        )
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "failed" and result.error == failure and not result.answer
        provider.classify.assert_awaited_once()
        provider.reply.assert_not_awaited()
        search.search.assert_not_awaited()
        fetch.assert_not_awaited()
        store.record_call.assert_awaited_once()
        store.settle.assert_not_awaited()

    asyncio.run(run())


def test_relevant_follow_up_classifies_with_topic_and_history_before_answering() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        turn.question = "gdzie mogę założyć ike?"
        store.context.return_value.text = "IKE można założyć w banku lub domu maklerskim."
        previous = turn.model_copy(
            update={"id": uuid4(), "question": "Co to jest IKE?", "status": "completed"}
        )
        store.history.return_value = [previous]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "completed"
        payload = provider.classify.await_args.args[0]
        assert payload.question == turn.question
        assert "IKE" in payload.passages["primary:1"].excerpt
        assert payload.history[0]["content"] == "Co to jest IKE?"
        assert [call.args[2] for call in store.reserve_call.await_args_list] == [
            "classification",
            "decision",
        ]
        provider.reply.assert_awaited_once()
        search.search.assert_not_awaited()

    asyncio.run(run())


def test_answer_budget_rejection_after_classification_cannot_make_an_answer_call() -> None:
    async def run() -> None:
        service, store, provider, fetch, search, turn = setup_chat()
        store.reserve_call.side_effect = [uuid4(), None]
        result = await service.ask(uuid4(), turn.item_id, turn.id, turn.question)
        assert result.status == "failed" and result.error == "budget_exhausted"
        provider.classify.assert_awaited_once()
        provider.reply.assert_not_awaited()
        search.search.assert_not_awaited()
        store.settle.assert_awaited_once()

    asyncio.run(run())
