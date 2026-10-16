"""Re-anchor exact quotations with whitespace or trailing omission markers."""

import re


def resolve_excerpt(source: str, excerpt: str) -> str | None:
    exact = _resolve_exact_excerpt(source, excerpt)
    if exact is not None:
        return exact
    trimmed = excerpt.rstrip()
    for marker in ("...", "…"):
        if trimmed.endswith(marker):
            candidate = trimmed.removesuffix(marker).rstrip()
            if 10 <= len(candidate) <= 2000:
                return _resolve_exact_excerpt(source, candidate)
    return None


def _resolve_exact_excerpt(source: str, excerpt: str) -> str | None:
    if not excerpt.strip():
        return None
    if excerpt in source:
        return excerpt
    characters: list[str] = []
    positions: list[int] = []
    for match in re.finditer(r"\S+", source):
        if characters:
            characters.append(" ")
            positions.append(match.start() - 1)
        characters.extend(match.group())
        positions.extend(range(match.start(), match.end()))
    normalized = " ".join(excerpt.split())
    start = "".join(characters).find(normalized)
    if start < 0:
        return None
    exact = source[positions[start] : positions[start + len(normalized) - 1] + 1]
    return exact if len(exact) <= 2000 else None
