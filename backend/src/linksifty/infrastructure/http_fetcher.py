"""Conservative public-web text acquisition."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from enum import StrEnum
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx


class FetchFailure(StrEnum):
    UNSAFE_URL = "unsafe_url"
    LOGIN_REQUIRED = "login_required"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class FetchResult:
    text: str | None = None
    failure: FetchFailure | None = None


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
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
    """Fetch public HTML only; callers map every failure to manual content."""
    target = _validated_url(url)
    if target is None:
        return FetchResult(failure=FetchFailure.UNSAFE_URL)
    host = target.raw_host.decode("ascii")
    try:
        addresses = await _addresses(host, target.port or (443 if target.scheme == "https" else 80))
    except (OSError, TimeoutError):
        return FetchResult(failure=FetchFailure.UNAVAILABLE)
    if not addresses or not all(_public_address(address) for address in addresses):
        return FetchResult(failure=FetchFailure.UNSAFE_URL)
    try:
        # A fresh client prevents credential/cookie leakage and cross-host TLS pool reuse.
        # Pin the socket destination; Host and SNI retain the original virtual host.
        async with httpx.AsyncClient(transport=transport, trust_env=False) as client:
            response = await client.get(
                target.copy_with(host=addresses[0]),
                headers={"Host": target.netloc.decode("ascii")},
                extensions={"sni_hostname": host},
                follow_redirects=False,
                timeout=10.0,
            )
    except httpx.HTTPError:
        return FetchResult(failure=FetchFailure.UNAVAILABLE)
    if response.status_code >= 400:
        return FetchResult(failure=FetchFailure.UNAVAILABLE)
    parser = _TextParser()
    parser.feed(response.text)
    text = " ".join(" ".join(parser.parts).split())
    if "log in" in text.lower() or "sign in" in text.lower():
        return FetchResult(failure=FetchFailure.LOGIN_REQUIRED)
    return FetchResult(text=text)
