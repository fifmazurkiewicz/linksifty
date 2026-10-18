"""A short query from public source prose, without transport provenance or post IDs."""

import re


def research_query(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(
            (
                "http://",
                "https://",
                "author_id=",
                "Submitted repost:",
                "quoted:",
                "replied_to:",
                "retweeted:",
                "Image source:",
                "Image URL:",
            )
        ):
            continue
        line = re.sub(r"https?://\S+|\b\d{10,}\b", " ", line)
        if not any(char.isalpha() for char in line):
            continue
        lines.append(" ".join(line.split()))
        if len(" ".join(lines)) >= 250:
            break
    return " ".join(lines)[:250]
