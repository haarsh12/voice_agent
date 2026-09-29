"""Network boundary for scheduled source checks, hardened against SSRF."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import socket
import ssl
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

import httpx
import truststore

from app.config.settings import Settings
from app.knowledge.contracts import FetchedDocument
from app.knowledge.registry import ApprovedSourceDefinition, canonicalize_url, is_approved_source_url

_SUPPORTED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/json",
    "application/xml",
    "text/xml",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


class SourceFetchError(RuntimeError):
    """A safe operational category; raw remote responses are never surfaced."""


async def fetch_approved_document(
    *,
    url: str,
    source: ApprovedSourceDefinition,
    settings: Settings,
    conditional_headers: dict[str, str] | None = None,
) -> FetchedDocument | None:
    """Fetch one allowlisted document with redirect, DNS, type, and size checks.

    A ``None`` result represents a valid HTTP 304 response. Every redirect is
    independently validated, so an approved government page cannot redirect a
    worker to an arbitrary host.
    """

    current_url = canonicalize_url(url)
    headers = {"User-Agent": "SahayakKnowledgeBot/1.0 (+verified-source-check)"}
    headers.update(conditional_headers or {})
    timeout = httpx.Timeout(settings.knowledge_fetch_timeout_seconds)
    # Windows and managed enterprise networks commonly install their trusted
    # inspection root in the OS store rather than certifi. truststore uses the
    # platform's verified roots; it never disables certificate validation.
    tls_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, verify=tls_context) as client:
        for _ in range(4):
            await _validate_fetch_destination(current_url, source)
            try:
                async with client.stream("GET", current_url, headers=headers) as response:
                    if response.status_code == 304:
                        return None
                    if response.status_code in _REDIRECT_STATUS_CODES:
                        location = response.headers.get("location")
                        if not location:
                            raise SourceFetchError("source_redirect_missing_location")
                        current_url = canonicalize_url(urljoin(current_url, location))
                        # Conditional headers apply only to the initial representation.
                        headers.pop("If-None-Match", None)
                        headers.pop("If-Modified-Since", None)
                        continue
                    if response.status_code < 200 or response.status_code >= 300:
                        raise SourceFetchError("source_http_error")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower().strip()
                    if content_type not in _SUPPORTED_CONTENT_TYPES:
                        raise SourceFetchError("source_content_type_rejected")
                    declared_size = response.headers.get("content-length")
                    if declared_size and (not declared_size.isdigit() or int(declared_size) > settings.knowledge_max_document_bytes):
                        raise SourceFetchError("source_document_too_large")
                    content = await _read_bounded(response, settings.knowledge_max_document_bytes)
                    return FetchedDocument(
                        url=current_url,
                        canonical_url=canonicalize_url(current_url),
                        content=content,
                        content_type=content_type,
                        content_hash=hashlib.sha256(content).hexdigest(),
                        etag=response.headers.get("etag"),
                        last_modified=response.headers.get("last-modified"),
                        fetched_at=datetime.now(UTC),
                    )
            except (httpx.HTTPError, OSError) as error:
                raise SourceFetchError("source_request_failed") from error
    raise SourceFetchError("source_redirect_limit_exceeded")


async def _validate_fetch_destination(url: str, source: ApprovedSourceDefinition) -> None:
    if not is_approved_source_url(url, source):
        raise SourceFetchError("source_url_not_approved")
    hostname = urlsplit(url).hostname
    if not hostname:
        raise SourceFetchError("source_url_invalid")
    try:
        addresses = await asyncio.get_running_loop().run_in_executor(
            None, lambda: socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        )
    except socket.gaierror as error:
        raise SourceFetchError("source_dns_failed") from error
    if not addresses:
        raise SourceFetchError("source_dns_failed")
    for address in {entry[4][0] for entry in addresses}:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as error:
            raise SourceFetchError("source_dns_invalid") from error
        if not parsed.is_global:
            raise SourceFetchError("source_private_address_rejected")


async def _read_bounded(response: httpx.Response, maximum_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > maximum_bytes:
            raise SourceFetchError("source_document_too_large")
        chunks.append(chunk)
    return b"".join(chunks)


def conditional_request_headers(*, etag: str | None, last_modified: str | None) -> dict[str, str]:
    """Build only safe standard validators for an incremental follow-up check."""

    headers: dict[str, str] = {}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    return headers


def parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
