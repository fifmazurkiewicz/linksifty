"""Conservative public-web text acquisition."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from linksifty.domain.acquisition import FetchFailure as FetchFailure
from linksifty.domain.acquisition import FetchResult as FetchResult
from linksifty.domain.acquisition import MediaType
from linksifty.domain.x_urls import X_HOSTS


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored: list[str] = []
        self.media: set[MediaType] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.ignored:
            if tag == "img":
                source = dict(attrs).get("src") or ""
                path = source.split("?", 1)[0].split("#", 1)[0]
                self.media.add("gif" if path.lower().endswith(".gif") else "image")
            elif tag in {"video", "audio"}:
                self.media.add("video" if tag == "video" else "audio")
            elif tag in {"iframe", "object", "embed"}:
                self.media.add("attachment")
        if tag in {"script", "style", "head", "nav", "footer", "aside", "noscript"}:
            self.ignored.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored:
            self.ignored = self.ignored[: self.ignored.index(tag)]

    def handle_data(self, data: str) -> None:
        if not self.ignored:
            self.parts.append(data)


def _public_address(host: str) -> bool:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        address.is_global
        and not address.is_multicast
        and not address.is_reserved
        and not (
            isinstance(address, ipaddress.IPv6Address)
            and (address.is_site_local or address.sixtofour is not None)
        )
    )


def _validated_url(url: str) -> httpx.URL | None:
    if "\\" in url or any(ord(char) <= 32 or ord(char) == 127 for char in url):
        return None
    try:
        parsed = urlparse(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or "@" in parsed.netloc
            or parsed.port == 0
        ):
            return None
        target = httpx.URL(url)
        host = target.raw_host.decode("ascii")
        if (
            "%" in host
            or host.rstrip(".") == "localhost"
            or host.rstrip(".").endswith(".localhost")
        ):
            return None
        return target
    except (ValueError, httpx.InvalidURL):
        return None


async def _addresses(host: str, port: int) -> tuple[str, ...]:
    try:
        return (str(ipaddress.ip_address(host)),)
    except ValueError:
        records = await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(
                host,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            ),
            timeout=10.0,
        )
        return tuple(str(record[4][0]) for record in records)


async def fetch_public_text(
    url: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FetchResult:
    """Bounded acquisition: validate and pin every redirect; never return partial bytes."""
    try:
        async with asyncio.timeout(60):
            return await _fetch(url, transport)
    except (httpx.HTTPError, TimeoutError, UnicodeError, ValueError):
        return FetchResult(failure=FetchFailure.UNAVAILABLE)


async def _fetch(url: str, transport: httpx.AsyncBaseTransport | None) -> FetchResult:
    for hop in range(6):
        target = _validated_url(url)
        if target is None:
            return FetchResult(failure=FetchFailure.UNSAFE_URL)
        host = target.raw_host.decode("ascii")
        if host.rstrip(".") in X_HOSTS:
            return FetchResult(failure=FetchFailure.UNSUPPORTED)
        try:
            addresses = await _addresses(
                host, target.port or (443 if target.scheme == "https" else 80)
            )
        except (OSError, TimeoutError):
            return FetchResult(failure=FetchFailure.UNAVAILABLE)
        if not addresses or not all(_public_address(address) for address in addresses):
            return FetchResult(failure=FetchFailure.UNSAFE_URL)
        # Fresh, proxy-free client pins the destination and isolates cookies per hop.
        async with httpx.AsyncClient(transport=transport, trust_env=False) as client:
            async with client.stream(
                "GET",
                target.copy_with(host=addresses[0]),
                headers={
                    "Host": target.netloc.decode("ascii"),
                    "Accept": "text/html,text/plain",
                    "Accept-Encoding": "identity",
                },
                extensions={"sni_hostname": host},
                follow_redirects=False,
                timeout=10,
            ) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location or hop == 5:
                        return FetchResult(failure=FetchFailure.UNAVAILABLE)
                    next_url = urljoin(str(target), location)
                    if target.scheme == "https" and urlparse(next_url).scheme != "https":
                        return FetchResult(failure=FetchFailure.UNSAFE_URL)
                    url = next_url
                    continue
                if response.status_code != 200:
                    return FetchResult(
                        failure=FetchFailure.PARTIAL
                        if response.status_code == 206
                        else FetchFailure.UNAVAILABLE
                    )
                mime = response.headers.get("content-type", "").split(";")[0].lower().strip()
                if mime and mime not in {"text/html", "text/plain", "application/xhtml+xml"}:
                    return FetchResult(failure=FetchFailure.UNSUPPORTED)
                # Bound raw response bytes; do not let an ignored identity request
                # trigger unbounded automatic decompression before our size check.
                if response.headers.get("content-encoding", "identity").lower() not in {
                    "identity",
                    "",
                }:
                    return FetchResult(failure=FetchFailure.UNSUPPORTED)
                length = response.headers.get("content-length")
                if length and int(length) > 500000:
                    return FetchResult(failure=FetchFailure.TOO_LARGE)
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 500000:
                        return FetchResult(failure=FetchFailure.TOO_LARGE)
                if (
                    length
                    and "content-encoding" not in response.headers
                    and len(body) != int(length)
                ):
                    return FetchResult(failure=FetchFailure.PARTIAL)
                if body.startswith((b"%PDF-", b"PK\x03\x04")):
                    return FetchResult(failure=FetchFailure.UNSUPPORTED)
                raw = bytes(body).decode(response.encoding or "utf-8", errors="strict")
                if "\x00" in raw:
                    return FetchResult(failure=FetchFailure.UNSUPPORTED)
        if "<html" in raw.lower() and "</html>" not in raw.lower():
            return FetchResult(failure=FetchFailure.PARTIAL)
        parser = _TextParser()
        parser.feed(raw)
        parser.close()
        text = " ".join(" ".join(parser.parts).split())
        if len(text.encode("utf-8")) > 100000:
            return FetchResult(failure=FetchFailure.TOO_LARGE)
        if "log in" in text.lower() or "sign in" in text.lower():
            return FetchResult(failure=FetchFailure.LOGIN_REQUIRED)
        return FetchResult(text=text, omitted_media=tuple(sorted(parser.media)))
    return FetchResult(failure=FetchFailure.UNAVAILABLE)
