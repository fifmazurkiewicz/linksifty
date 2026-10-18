"""X source identity; no credentials or network access."""

import re
from urllib.parse import urlsplit

X_HOSTS = frozenset(
    {
        "x.com",
        "www.x.com",
        "mobile.x.com",
        "twitter.com",
        "www.twitter.com",
        "mobile.twitter.com",
        "m.twitter.com",
    }
)
_POST_PATH = re.compile(r"/(?:[A-Za-z0-9_]{1,15}|i/web)/status/([0-9]{1,19})/?")


def is_x_url(url: str) -> bool:
    try:
        return (urlsplit(url).hostname or "").rstrip(".") in X_HOSTS
    except ValueError:
        return False


def x_post_id(url: str) -> str | None:
    if "\\" in url or any(ord(char) <= 32 or ord(char) == 127 for char in url):
        return None
    try:
        parsed = urlsplit(url)
        if (
            not is_x_url(url)
            or parsed.scheme not in {"http", "https"}
            or "@" in parsed.netloc
            or parsed.port not in {None, 80 if parsed.scheme == "http" else 443}
        ):
            return None
        match = _POST_PATH.fullmatch(parsed.path)
        return match[1] if match else None
    except ValueError:
        return None
