"""Saved-context answers with at most two durable, conditional searches per question."""

import asyncio
import hashlib
import logging
import re
from collections.abc import Awaitable, Callable
from contextlib import nullcontext
from decimal import Decimal
from typing import Literal
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from linksifty.application.chat_contracts import (
    CallSlot,
    ChatCitation,
    ChatClassification,
    ChatContext,
    ChatDraft,
    ChatError,
    ChatHistory,
    ChatInput,
    ChatParagraph,
    ChatProvider,
    ChatStore,
    ChatTurn,
)
from linksifty.application.processing_contracts import EvidenceSource, Telemetry
from linksifty.application.research_contracts import SearchProvider
from linksifty.domain.acquisition import FetchResult
from linksifty.domain.content_policy import ContentReadiness, evaluate_content

_logger = logging.getLogger(__name__)


def _refusal(classification: ChatClassification) -> ChatParagraph:
    if classification.category == "unsafe":
        text = (
            "Nie mogę pomóc w działaniach, które mogłyby kogoś skrzywdzić. "
            "Mogę pomóc z bezpiecznym pytaniem dotyczącym tej analizy lub jej tematu."
            if classification.language == "pl"
            else "I can't help with actions that could harm someone. "
            "I can help with a safe question about this analysis or its topic."
        )
    else:
        text = (
            "Chętnie pomogę z pytaniem dotyczącym tej analizy lub jej tematu. "
            "Zadaj proszę pytanie w tym zakresie."
            if classification.language == "pl"
            else "I'm happy to help with questions about this analysis or its topic. "
            "Please ask a question within that scope."
        )
    return ChatParagraph(text=text, citations=[])


def _url_key(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def _input(context: ChatContext, turns: list[ChatTurn], question: str) -> ChatInput:
    # Bounded excerpts, not a claim that every saved page fits the model context.
    sources = {source.url: source for source in context.sources}
    for turn in turns:
        for source in turn.sources:
            sources[source.url] = source
    words = set(re.findall(r"\w{3,}", question.lower()))
    ranked = sorted(
        sources.values(),
        key=lambda source: len(words & set(re.findall(r"\w{3,}", source.text.lower()))),
        reverse=True,
    )[:30]
    documents = [
        (
            "analysis",
            None,
            "Saved analysis",
            context.assessment.model_dump_json(exclude={"citations"}),
        ),
        ("primary", context.url, "Original source", context.text),
        *[
            (f"chat{i}", source.url, "Research source", source.text)
            for i, source in enumerate(ranked, 1)
        ],
    ]
    passages: dict[str, ChatCitation] = {}
    for prefix, url, label, text in documents:
        limit = (
            18000
            if prefix == "analysis"
            else 12000
            if prefix == "primary"
            else 24000 // max(1, len(ranked))
        )
        chunks = list(
            enumerate((text[start : start + 1000] for start in range(0, len(text), 1000)), 1)
        )
        chunks.sort(
            key=lambda chunk: len(words & set(re.findall(r"\w{3,}", chunk[1].lower()))),
            reverse=True,
        )
        selected: list[tuple[int, str]] = []
        for index, chunk in chunks:
            if limit <= 0:
                break
            bounded = chunk.encode()[:limit].decode("utf-8", errors="ignore")
            selected.append((index, bounded))
            limit -= len(bounded.encode())
        for index, bounded in sorted(selected):
            identifier = f"{prefix}:{index}"
            passages[identifier] = ChatCitation(
                passage_id=identifier,
                excerpt=bounded,
                source_url=url,
                label=label,
            )
    history: list[dict[str, str]] = []
    for turn in turns[-8:]:
        if turn.status == "completed":
            history.extend(
                [
                    {
                        "role": "user",
                        "content": turn.question.encode()[:1000].decode("utf-8", errors="ignore"),
                    },
                    {
                        "role": "assistant",
                        "content": "\n".join(p.text for p in turn.answer)
                        .encode()[:2500]
                        .decode("utf-8", errors="ignore"),
                    },
                ]
            )
    return ChatInput(question=question, passages=passages, history=history)


class ChatService:
    def __init__(
        self,
        store: ChatStore,
        provider: ChatProvider | None,
        fetch: Callable[[str], Awaitable[FetchResult]],
        *,
        search: SearchProvider | None = None,
        search_price: Decimal = Decimal(0),
        telemetry: Telemetry | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._store = store
        self._provider = provider
        self._fetch = fetch
        self._search = search
        self._search_price = search_price

    @property
    def search_available(self) -> bool:
        return self._search is not None and self._search_price > 0

    async def history(self, user_id: UUID, item_id: UUID) -> ChatHistory:
        if await self._store.context(user_id, item_id) is None:
            raise ChatError("not_found")
        return ChatHistory(
            turns=await self._store.history(user_id, item_id),
            available=self._provider is not None,
            search_available=self.search_available,
            search_price_usd=self._search_price if self.search_available else None,
        )

    async def ask(
        self,
        user_id: UUID,
        item_id: UUID,
        request_id: UUID,
        question: str,
        *,
        max_searches: Literal[1, 2] = 1,
    ) -> ChatTurn:
        context = await self._store.context(user_id, item_id)
        if context is None:
            raise ChatError("not_found")
        if self._provider is None:
            raise ChatError("unavailable")
        try:
            self._provider.chat_estimate()
        except ValueError as failure:
            raise ChatError("unavailable") from failure
        claim = await self._store.claim_turn(user_id, item_id, request_id, question)
        if claim is None:
            raise ChatError("busy")
        turn = claim.turn
        if turn.question != question:
            raise ChatError("request_conflict")
        if not claim.claimed:
            return turn
        with self._telemetry.scope("chat", str(turn.id)) if self._telemetry else nullcontext():
            status: Literal["completed", "failed"] = "failed"
            answer: list[ChatParagraph] = []
            sources: list[EvidenceSource] = []
            search_status = "not_needed"
            insufficient = False
            error: str | None = None
            try:
                turns = await self._store.history(user_id, item_id)
                payload = _input(context, turns, question)
                classification = await self._classify(user_id, turn, payload)
                if classification.category != "relevant":
                    answer = [_refusal(classification)]
                else:
                    payload.reply_language = classification.language
                    allow_search = self.search_available
                    draft = await self._generate(user_id, turn, "decision", payload, allow_search)
                    queries: list[str] = []
                    while draft.search_query is not None:
                        if (
                            not allow_search
                            or not draft.search_query.strip()
                            or draft.paragraphs
                            or draft.insufficient
                        ):
                            raise ChatError("invalid_answer")
                        query = " ".join(draft.search_query.split())
                        if query.casefold() in {q.casefold() for q in queries}:
                            draft = ChatDraft(search_query=None, paragraphs=[], insufficient=True)
                            break
                        new_sources, search_status = await self._research(
                            user_id,
                            turn,
                            query,
                            context,
                            turns,
                            slot="search" if not queries else "search_refined",
                        )
                        if search_status == "budget_exhausted":
                            draft = ChatDraft(search_query=None, paragraphs=[], insufficient=True)
                            break
                        queries.append(query)
                        sources.extend(new_sources)
                        context.sources.extend(new_sources)
                        payload = _input(context, turns, question)
                        payload.reply_language = classification.language
                        payload.search_queries = list(queries)
                        allow_search = len(queries) < max_searches and search_status in {
                            "ready",
                            "no_sources",
                        }
                        draft = await self._generate(
                            user_id,
                            turn,
                            "answer" if len(queries) == 1 else "answer_final",
                            payload,
                            allow_search,
                        )
                    if draft.search_query is not None or (
                        not draft.paragraphs and not draft.insufficient
                    ):
                        raise ChatError("invalid_answer")
                    for paragraph in draft.paragraphs:
                        if not paragraph.text.strip() or any(
                            pid not in payload.passages for pid in paragraph.passage_ids
                        ):
                            raise ChatError("invalid_evidence")
                        answer.append(
                            ChatParagraph(
                                text=paragraph.text,
                                citations=[
                                    payload.passages[pid]
                                    for pid in dict.fromkeys(paragraph.passage_ids)
                                ],
                            )
                        )
                    insufficient = draft.insufficient
                status = "completed"
            except ChatError as failure:
                error = str(failure)
                answer = []
            # Infrastructure errors intentionally propagate. The durable pending turn
            # expires on read; its reservations survive and no provider is resent.
            saved = await self._store.finish(
                user_id,
                turn,
                status=status,
                answer=answer,
                insufficient=insufficient,
                search_status=search_status,
                sources=sources,
                error=error,
            )
            if saved is None:
                raise ChatError("not_found")  # Deleted/rejected/expired during the request.
            if self._telemetry is not None:
                self._telemetry.event(
                    "chat.finished",
                    {
                        "status": saved.status,
                        "failure": saved.error,
                        "search_status": saved.search_status,
                    },
                )
            if saved.status == "failed":
                _logger.warning("chat_failed turn_id=%s reason=%s", turn.id, saved.error)
            return saved

    async def _generate(
        self, user_id: UUID, turn: ChatTurn, slot: CallSlot, payload: ChatInput, allow_search: bool
    ) -> ChatDraft:
        if self._provider is None:
            raise ChatError("unavailable")
        try:
            amount = self._provider.chat_estimate()
        except ValueError as failure:
            raise ChatError("unavailable") from failure
        reservation = await self._store.reserve_call(user_id, turn, slot, amount)
        if reservation is None:
            raise ChatError("budget_exhausted")
        result = await self._provider.reply(payload, allow_search=allow_search)
        await self._store.record_call(user_id, reservation, result.generation_id)
        if result.cost is not None:
            await self._store.settle(user_id, reservation, result.cost)
        if result.draft is None or result.failure_reason:
            raise ChatError(result.failure_reason or "invalid_answer")
        return result.draft

    async def _classify(
        self, user_id: UUID, turn: ChatTurn, payload: ChatInput
    ) -> ChatClassification:
        if self._provider is None:
            raise ChatError("unavailable")
        reservation = await self._store.reserve_call(
            user_id, turn, "classification", self._provider.classification_estimate()
        )
        if reservation is None:
            raise ChatError("budget_exhausted")
        result = await self._provider.classify(payload)
        await self._store.record_call(user_id, reservation, result.generation_id)
        if result.cost is not None:
            await self._store.settle(user_id, reservation, result.cost)
        if result.classification is None or result.failure_reason:
            raise ChatError(result.failure_reason or "invalid_classification")
        return result.classification

    async def _research(
        self,
        user_id: UUID,
        turn: ChatTurn,
        query: str,
        context: ChatContext,
        turns: list[ChatTurn],
        *,
        slot: Literal["search", "search_refined"],
    ) -> tuple[list[EvidenceSource], str]:
        if self._search is None:
            return [], "unavailable"
        reservation = await self._store.reserve_call(user_id, turn, slot, self._search_price)
        if reservation is None:
            return [], "budget_exhausted"
        # Exactly one request. An uncertain response is never retried.
        response = await self._search.search(query)
        if not response.confirmed:
            return [], "uncertain"
        await self._store.settle(user_id, reservation, self._search_price)
        existing = [*context.sources, *(source for t in turns for source in t.sources)]
        urls = {_url_key(source.url) for source in existing}
        if context.url:
            urls.add(_url_key(context.url))
        candidates = []
        for url in response.urls[:20]:
            try:
                key = _url_key(url)
                if key not in urls:
                    candidates.append(url)
                    urls.add(key)
            except ValueError:
                continue
        semaphore = asyncio.Semaphore(4)

        async def acquire(url: str) -> EvidenceSource | None:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(self._fetch(url), timeout=10)
                    if result.failure is not None or result.text is None:
                        return None
                    if (
                        evaluate_content(result.text, fetched=True).readiness
                        != ContentReadiness.READY
                    ):
                        return None
                    text = result.text.encode()[:12000].decode("utf-8", errors="ignore")
                    return EvidenceSource(id="chat", url=url, text=text)
                except (TimeoutError, ValueError):
                    return None

        results = await asyncio.gather(*(acquire(url) for url in candidates))
        hashes = {hashlib.sha256(" ".join(s.text.split()).encode()).digest() for s in existing}
        hashes.add(hashlib.sha256(" ".join(context.text.split()).encode()).digest())
        sources = []
        for source in results:
            if source is not None:
                digest = hashlib.sha256(" ".join(source.text.split()).encode()).digest()
                if digest not in hashes:
                    sources.append(source)
                    hashes.add(digest)
        return sources, "ready" if sources else "no_sources"
