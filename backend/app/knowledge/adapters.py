"""Reviewed, one-hop document discovery for each approved source group.

Discovery is deliberately not a crawler. Each source has reviewed entry pages
and permitted document-path prefixes in ``registry.py``. We parse links from
those entry pages only, reject anything outside that source's approved HTTPS
domains, and cap scheduled work for each source check.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from app.knowledge.registry import (
    ApprovedSourceDefinition,
    canonicalize_url,
    is_approved_source_url,
)


class SourceAdapter:
    """Finite, source-specific discovery boundary for scheduled ingestion."""

    def documents_to_check(self, source: ApprovedSourceDefinition) -> tuple[str, ...]:
        """Return reviewed source entry pages, never a user-provided URL."""

        return source.entry_urls

    def discover_documents(
        self,
        *,
        source: ApprovedSourceDefinition,
        entry_url: str,
        content: bytes,
        content_type: str,
    ) -> tuple[str, ...]:
        """Extract a bounded document set linked by one reviewed entry page."""

        if content_type not in {"text/html", "application/xhtml+xml"}:
            return ()
        parser = _ApprovedLinkParser()
        try:
            parser.feed(content.decode("utf-8", errors="replace"))
            parser.close()
        except Exception:
            # A broken page must never expand discovery to arbitrary URLs.
            return ()

        discovered: list[str] = []
        seen: set[str] = set()
        for href in parser.hrefs:
            candidate = _reviewed_document_url(
                href=href,
                entry_url=entry_url,
                source=source,
            )
            if candidate is None or candidate in seen:
                continue
            seen.add(candidate)
            discovered.append(candidate)
            if len(discovered) >= source.max_documents_per_check:
                break
        return tuple(discovered)


class _ApprovedLinkParser(HTMLParser):
    """Collect hyperlinks only; parsing never executes source-page content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.hrefs.append(value.strip())
                return


def _reviewed_document_url(
    *,
    href: str,
    entry_url: str,
    source: ApprovedSourceDefinition,
) -> str | None:
    """Validate one discovered link against its source's reviewed path scope."""

    if not href or href.startswith(("#", "javascript:", "data:", "mailto:")):
        return None
    try:
        candidate = canonicalize_url(urljoin(entry_url, href))
        parsed = urlsplit(candidate)
    except ValueError:
        return None
    if not is_approved_source_url(candidate, source):
        return None
    path = (parsed.path or "/").casefold()
    prefixes = tuple(prefix.casefold() for prefix in source.discovery_path_prefixes)
    if not prefixes or not any(path.startswith(prefix) for prefix in prefixes):
        return None
    return candidate


DEFAULT_SOURCE_ADAPTER = SourceAdapter()
