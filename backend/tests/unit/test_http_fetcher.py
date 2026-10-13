import asyncio
import socket
from collections.abc import Callable
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from linksifty.infrastructure.http_fetcher import FetchFailure, FetchResult, fetch_public_text

PUBLIC_IP = "93.184.216.34"


@pytest.fixture(autouse=True)
def public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    def resolve(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_IP, 443))]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)


def fetch(
    url: str,
    handler: Callable[[httpx.Request], httpx.Response] | None = None,
) -> FetchResult:
    async def run() -> FetchResult:
        transport = httpx.MockTransport(handler or (lambda _: httpx.Response(200, text="hello")))
        return await fetch_public_text(url, transport=transport)

    return asyncio.run(run())


def test_login_page_requires_manual_content() -> None:
    result = fetch("https://example.com/a", lambda _: httpx.Response(200, text="Please log in"))
    assert result.failure is FetchFailure.LOGIN_REQUIRED
    assert result.text is None


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/private",
        "http://10.0.0.1",
        "http://169.254.169.254",
        "http://100.64.0.1",
        "http://0.0.0.0",
        "http://224.0.0.1",
        "http://[::1]",
        "http://[fc00::1]",
        "http://[fe80::1]",
        "http://[fec0::1]",
        "http://[ff02::1]",
        "http://[::ffff:127.0.0.1]",
        "http://[2002:7f00:1::]",
        "http://localhost",
        "http://LOCALHOST./",
        "http://example.com@127.0.0.1",
        "https://user:pass@example.com",
        "https://@example.com",
        "file:///etc/hosts",
        "https://",
        "https://[broken",
        "https://example.com:bad",
        "https://example.com:65536",
        "https://example.com:0",
        "https://example.com\\@127.0.0.1",
        "https://example.com/\nheader",
    ],
)
def test_unsafe_urls_never_reach_transport(url: str) -> None:
    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("unsafe URL reached transport")

    result = fetch(url, forbidden)
    assert result.failure is FetchFailure.UNSAFE_URL
    assert result.text is None


@pytest.mark.parametrize(
    "addresses",
    [[], ["127.0.0.1"], ["::1"], [PUBLIC_IP, "10.0.0.1"], [PUBLIC_IP, "::ffff:127.0.0.1"]],
)
def test_all_dns_answers_must_be_public(
    monkeypatch: pytest.MonkeyPatch, addresses: list[str]
) -> None:
    def resolve(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in addresses]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)

    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("unsafe DNS reached transport")

    result = fetch("https://example.com", forbidden)
    assert result.failure is FetchFailure.UNSAFE_URL
    assert result.text is None


def test_dns_failure_requires_manual_content(monkeypatch: pytest.MonkeyPatch) -> None:
    def resolve(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        raise socket.gaierror("test resolution failure")

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    result = fetch("https://example.com")
    assert result.failure is FetchFailure.UNAVAILABLE
    assert result.text is None


@pytest.mark.parametrize("ip", [PUBLIC_IP, "2606:4700:4700::1111"])
def test_connection_is_pinned_and_preserves_hostname(
    monkeypatch: pytest.MonkeyPatch, ip: str
) -> None:
    lookups: list[str] = []

    def resolve(host: str, *args: object, **kwargs: object) -> list[tuple[object, ...]]:
        lookups.append(host)
        # A second hostname resolution would be a rebinding attack.
        resolved = ip if len(lookups) == 1 else "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (resolved, 8443))]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.host == ip
        assert request.url.port == 8443
        assert request.url.raw_path == b"/article?q=1"
        assert request.headers["host"] == "example.com:8443"
        assert request.extensions["sni_hostname"] == "example.com"
        return httpx.Response(200, text="<p>Public content</p>")

    result = fetch("https://example.com:8443/article?q=1", respond)
    assert result == FetchResult(text="Public content")
    assert lookups == ["example.com"]


def test_real_transport_connects_to_pinned_ip_and_validates_original_tls_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = Mock()
    stream.read = AsyncMock(return_value=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello")
    stream.write = AsyncMock()
    stream.aclose = AsyncMock()
    stream.start_tls = AsyncMock(return_value=stream)
    stream.get_extra_info.return_value = None
    connections: list[tuple[str, int]] = []

    async def connect(self: object, host: str, port: int, **kwargs: object) -> Mock:
        connections.append((host, port))
        return stream

    monkeypatch.setattr("httpcore._backends.auto.AutoBackend.connect_tcp", connect)
    # Environment proxies must not route acquisition around the pinned connection.
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9999")
    result = asyncio.run(fetch_public_text("https://example.com/a"))
    assert result == FetchResult(text="hello")
    assert connections == [(PUBLIC_IP, 443)]
    assert stream.start_tls.call_args.kwargs["server_hostname"] == "example.com"
    assert stream.start_tls.call_args.kwargs["ssl_context"].check_hostname


def test_dns_timeout_requires_manual_content(monkeypatch: pytest.MonkeyPatch) -> None:
    async def timeout(host: str, port: int) -> tuple[str, ...]:
        raise TimeoutError

    monkeypatch.setattr("linksifty.infrastructure.http_fetcher._addresses", timeout)
    result = fetch("https://example.com")
    assert result.failure is FetchFailure.UNAVAILABLE
    assert result.text is None


def test_public_literal_ip_does_not_use_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        pytest.fail("literal IP must not resolve a hostname")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    assert fetch(f"https://{PUBLIC_IP}/a") == FetchResult(text="hello")
