"""Search discovery boundary; results alone are not evidence."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchResponse:
    confirmed: bool = False
    urls: tuple[str, ...] = ()


class SearchProvider(Protocol):
    async def search(self, query: str) -> SearchResponse: ...
