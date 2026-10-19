"""Owner-scoped research chat boundaries, independent of HTTP and provider SDKs."""

from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from linksifty.application.processing_contracts import AssessmentView, EvidenceSource


class ChatCitation(BaseModel):
    passage_id: str
    excerpt: str
    source_url: str | None = None
    label: str = "Source passage"


class ChatParagraph(BaseModel):
    text: str
    citations: list[ChatCitation]


class DraftParagraph(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=3000)
    passage_ids: list[str] = Field(min_length=1, max_length=8)


class ChatDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    search_query: str | None = Field(max_length=250)
    paragraphs: list[DraftParagraph] = Field(max_length=8)
    insufficient: bool


class ChatModelResult(BaseModel):
    draft: ChatDraft | None = None
    cost: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    generation_id: str | None = None
    failure_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ChatClassification(BaseModel):
    category: Literal["relevant", "off_topic", "unsafe"]
    language: Literal["pl", "en"]


class ChatClassificationResult(BaseModel):
    classification: ChatClassification | None = None
    cost: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    generation_id: str | None = None
    failure_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ChatTurn(BaseModel):
    id: UUID
    item_id: UUID
    question: str
    status: Literal["pending", "completed", "failed"]
    answer: list[ChatParagraph] = Field(default_factory=list)
    insufficient: bool = False
    search_status: str = "not_needed"
    error: str | None = None
    sources: list[EvidenceSource] = Field(default_factory=list, exclude=True)


class ChatClaim(BaseModel):
    turn: ChatTurn
    claimed: bool


class ChatHistory(BaseModel):
    turns: list[ChatTurn]
    available: bool
    search_available: bool
    search_price_usd: Decimal | None = None


class ChatContext(BaseModel):
    text: str
    url: str | None = None
    assessment: AssessmentView
    sources: list[EvidenceSource] = Field(default_factory=list)


class ChatInput(BaseModel):
    question: str
    passages: dict[str, ChatCitation]
    history: list[dict[str, str]]
    reply_language: Literal["pl", "en"] | None = None
    search_queries: list[str] = Field(default_factory=list, max_length=2)


class ChatError(Exception):
    """Stable application failure translated by HTTP at the edge."""


CallSlot = Literal[
    "classification", "decision", "search", "answer", "search_refined", "answer_final"
]


class ChatStore(Protocol):
    async def context(self, user_id: UUID, item_id: UUID) -> ChatContext | None: ...
    async def history(self, user_id: UUID, item_id: UUID) -> list[ChatTurn]: ...
    async def claim_turn(
        self, user_id: UUID, item_id: UUID, request_id: UUID, question: str
    ) -> ChatClaim | None: ...
    async def reserve_call(
        self, user_id: UUID, turn: ChatTurn, slot: CallSlot, amount: Decimal
    ) -> UUID | None: ...
    async def record_call(
        self, user_id: UUID, reservation_id: UUID, generation_id: str | None
    ) -> None: ...
    async def settle(self, user_id: UUID, reservation_id: UUID, cost: Decimal) -> None: ...
    async def finish(
        self,
        user_id: UUID,
        turn: ChatTurn,
        *,
        status: Literal["completed", "failed"],
        answer: list[ChatParagraph],
        insufficient: bool,
        search_status: str,
        sources: list[EvidenceSource],
        error: str | None,
    ) -> ChatTurn | None: ...


class ChatProvider(Protocol):
    def chat_estimate(self) -> Decimal: ...
    def classification_estimate(self) -> Decimal: ...
    async def classify(self, context: ChatInput) -> ChatClassificationResult: ...
    async def reply(self, context: ChatInput, *, allow_search: bool) -> ChatModelResult: ...
