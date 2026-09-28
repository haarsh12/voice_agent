"""Source-specific discovery boundary; the initial adapter is deliberately narrow."""

from __future__ import annotations

from typing import Protocol

from app.knowledge.registry import ApprovedSourceDefinition


class SourceAdapter(Protocol):
    """Discover only pre-reviewed documents for one source group."""

    def documents_to_check(self, source: ApprovedSourceDefinition) -> tuple[str, ...]:
        """Return a finite, allowlisted set of source URLs."""


class EntryUrlSourceAdapter:
    """Initial production adapter: checks registry entry documents only.

    This intentionally does not crawl arbitrary links from a government page.
    More focused source adapters can be introduced after their document paths
    and extraction behavior are reviewed and added to the registry.
    """

    def documents_to_check(self, source: ApprovedSourceDefinition) -> tuple[str, ...]:
        return source.entry_urls


DEFAULT_SOURCE_ADAPTER: SourceAdapter = EntryUrlSourceAdapter()
