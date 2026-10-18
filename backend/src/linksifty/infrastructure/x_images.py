"""Bounded credential-free acquisition of static images from X's media CDN."""

import asyncio
import io
import warnings
from urllib.parse import urlsplit

import httpx
from PIL import Image

from linksifty.domain.acquisition import FetchFailure, SourceImage
from linksifty.infrastructure.x_content import XContentFailure, XMedia

MAX_IMAGES = 4
_MAX_BYTES = 5_000_000
_MAX_TOTAL_BYTES = 10_000_000
_FORMATS = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}


def _unavailable() -> XContentFailure:
    return XContentFailure(FetchFailure.X_MEDIA_UNAVAILABLE, "media_bytes_unavailable_or_invalid")


def _validate(data: bytes, mime: str) -> None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=list(_FORMATS.values())) as image:
                if (
                    image.format != _FORMATS[mime]
                    or image.width * image.height > 20_000_000
                    or getattr(image, "n_frames", 1) != 1
                ):
                    raise _unavailable()
                image.verify()
            with Image.open(io.BytesIO(data), formats=list(_FORMATS.values())) as image:
                image.load()
    except (
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise _unavailable() from error


def validate_media(media: XMedia) -> str:
    if media.type != "photo":
        raise XContentFailure(FetchFailure.X_MEDIA_UNSUPPORTED, "non_static_image")
    url = media.url or ""
    try:
        target = urlsplit(url)
        if (
            target.scheme != "https"
            or target.hostname != "pbs.twimg.com"
            or target.port not in {None, 443}
            or target.username is not None
            or target.password is not None
            or target.fragment
            or "\\" in url
            or any(ord(char) <= 32 or ord(char) == 127 for char in url)
        ):
            raise _unavailable()
    except ValueError as error:
        raise _unavailable() from error
    return url


async def fetch_images(
    client: httpx.AsyncClient, media: list[tuple[XMedia, str]]
) -> tuple[SourceImage, ...]:
    unique: dict[str, str] = {}
    for item, source_url in media:
        url = validate_media(item)
        unique.setdefault(url, source_url)
    if len(unique) > MAX_IMAGES:
        raise XContentFailure(FetchFailure.TOO_LARGE, "image_count_limit")
    images: list[SourceImage] = []
    total = 0
    for url, source_url in unique.items():
        client.cookies.clear()
        async with client.stream(
            "GET",
            url,
            headers={"Accept": ",".join(_FORMATS), "Accept-Encoding": "identity"},
            follow_redirects=False,
            timeout=10,
        ) as response:
            mime = response.headers.get("content-type", "").split(";", 1)[0].lower().strip()
            if (
                response.status_code != 200
                or mime not in _FORMATS
                or response.headers.get("content-encoding", "identity") not in {"identity", ""}
            ):
                raise _unavailable()
            length = response.headers.get("content-length")
            if length is not None and (not length.isdigit() or int(length) > _MAX_BYTES):
                raise _unavailable()
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                total += len(chunk)
                if len(data) > _MAX_BYTES or total > _MAX_TOTAL_BYTES:
                    raise XContentFailure(FetchFailure.TOO_LARGE, "image_byte_limit")
            if length is not None and len(data) != int(length):
                raise _unavailable()
            raw = bytes(data)
            await asyncio.to_thread(_validate, raw, mime)
            images.append(SourceImage(url=url, source_url=source_url, mime_type=mime, data=raw))
    return tuple(images)
