"""Focused coverage for the source-grounded knowledge-engine safeguards."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from io import BytesIO

from pypdf import PdfWriter

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthBase
from app.config.settings import Settings
from app.knowledge.chunking import chunk_semantically
from app.knowledge.contracts import (
    Citation,
    DocumentStatus,
    ExtractedSourceDocument,
    FetchedDocument,
    RetrievedEvidence,
    RetrievalResult,
    SourceValidationStatus,
)
from app.knowledge.adapters import DEFAULT_SOURCE_ADAPTER
from app.knowledge.extraction import extract_source_document
from app.knowledge.models import KnowledgeSource
from app.knowledge.policy import decide_response
from app.knowledge.registry import SOURCE_REGISTRY, SOURCES_BY_KEY, is_approved_source_url
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.vectors import VertexEmbeddingProvider
import app.knowledge.vectors as vectors_module


def test_source_registry_contains_exactly_the_ten_approved_source_groups() -> None:
    assert len(SOURCE_REGISTRY) == 10
    assert set(SOURCES_BY_KEY) == {
        "ministry_of_cooperation",
        "national_cooperative_database",
        "central_registrar_of_cooperative_societies",
        "india_code",
        "state_rcs",
        "pmfby",
        "ministry_of_agriculture",
        "myscheme",
        "reserve_bank_of_india",
        "cpgrams",
    }
    assert SOURCES_BY_KEY["pmfby"].check_interval_hours == 24
    assert SOURCES_BY_KEY["india_code"].check_interval_hours == 24 * 7


def test_every_reviewed_source_category_has_an_explicit_crawl_target() -> None:
    for source in SOURCE_REGISTRY:
        assert source.crawl_targets
        target_categories = {category for target in source.crawl_targets for category in target.categories}
        assert set(source.expected_categories).issubset(target_categories)
        assert all(is_approved_source_url(target.url, source) for target in source.crawl_targets)


def test_registry_rejects_userinfo_http_and_unapproved_redirect_targets() -> None:
    source = SOURCES_BY_KEY["pmfby"]
    assert is_approved_source_url("https://pmfby.gov.in/", source)
    assert not is_approved_source_url("http://pmfby.gov.in/", source)
    assert not is_approved_source_url("https://pmfby.gov.in@attacker.example/", source)
    assert not is_approved_source_url("https://attacker.example/pmfby.gov.in", source)


def test_source_discovery_is_one_hop_path_scoped_and_rejects_external_links() -> None:
    source = SOURCES_BY_KEY["pmfby"]
    links = b"""
        <a href='/notification/latest-guidelines.pdf'>approved</a>
        <a href='/not-a-reviewed-path.pdf'>rejected</a>
        <a href='https://attacker.example/notification/forged.pdf'>rejected</a>
        <a href='javascript:alert(1)'>rejected</a>
    """

    discovered = DEFAULT_SOURCE_ADAPTER.discover_documents(
        source=source,
        entry_url="https://pmfby.gov.in/",
        content=links,
        content_type="text/html",
    )

    assert discovered == ("https://pmfby.gov.in/notification/latest-guidelines.pdf",)


def test_semantic_chunking_keeps_heading_with_its_related_paragraphs() -> None:
    chunks = chunk_semantically(
        "ELIGIBILITY\n\nFarmers must check the current official notification.\n\n"
        "CLAIM PROCESS\n\nKeep the acknowledgement and follow the applicable instructions."
    )

    assert len(chunks) == 2
    assert chunks[0].heading == "ELIGIBILITY"
    assert "Farmers" in chunks[0].content
    assert chunks[1].heading == "CLAIM PROCESS"


def test_semantic_chunking_preserves_pdf_page_numbers() -> None:
    chunks = chunk_semantically(
        "FIRST PAGE\n\nThis is enough text to remain with its official page."
        "\fSECOND PAGE\n\nThis is separate official source text."
    )

    assert [chunk.page_number for chunk in chunks] == [1, 2]


def test_scanned_pdf_uses_only_the_configured_ocr_adapter() -> None:
    class FakeOcr:
        def extract_pdf(self, document: FetchedDocument) -> ExtractedSourceDocument:
            assert document.url == "https://pmfby.gov.in/notification/scan.pdf"
            return ExtractedSourceDocument(
                text="OCR page text",
                title="Scanned circular",
                page_count=1,
                extraction_method="fake_ocr",
                is_ocr=True,
                ocr_confidence=0.98,
            )

    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)
    content = buffer.getvalue()
    document = FetchedDocument(
        url="https://pmfby.gov.in/notification/scan.pdf",
        canonical_url="https://pmfby.gov.in/notification/scan.pdf",
        content=content,
        content_type="application/pdf",
        content_hash=hashlib.sha256(content).hexdigest(),
        fetched_at=datetime.now(UTC),
    )

    extracted = extract_source_document(document, ocr_provider=FakeOcr())

    assert extracted.extraction_method == "fake_ocr"
    assert extracted.is_ocr is True


def test_embedding_provider_splits_a_provider_rejected_batch_without_reordering(monkeypatch) -> None:
    class FakeModels:
        def embed_content(self, *, model: str, contents: list[str]) -> object:
            del model
            if len(contents) > 1:
                raise RuntimeError("request batch too large")
            return type("Response", (), {"embeddings": [type("Embedding", (), {"values": [float(len(contents[0]))] + [1.0] * 63})()]})()

    fake_client = type("Client", (), {"models": FakeModels()})()
    monkeypatch.setattr(vectors_module, "create_gemini_client", lambda _: fake_client)
    provider = VertexEmbeddingProvider(
        Settings(knowledge_embedding_dimensions=64, knowledge_embedding_batch_size=4)
    )

    vectors = provider.embed(["a", "bb", "ccc"])

    assert [vector[0] for vector in vectors] == [1.0, 2.0, 3.0]
    assert all(len(vector) == 64 for vector in vectors)


def test_policy_abstains_on_an_unverified_current_scheme_question() -> None:
    decision = decide_response(
        message="What is the current PMFBY claim procedure and deadline?",
        language="en-IN",
        retrieval=RetrievalResult(),
    )

    assert decision.requires_abstention is True
    assert decision.evidence_status.value == "INSUFFICIENT_EVIDENCE"
    assert decision.abstention_message and "could not verify" in decision.abstention_message.casefold()


def test_policy_does_not_present_new_bank_website_information_as_general_guidance() -> None:
    decision = decide_response(
        message="मुझे पीएनबी वेबसाइट से नई जानकारी बताओ",
        language="hi-IN",
        retrieval=RetrievalResult(),
    )

    assert decision.requires_abstention is True
    assert decision.evidence_status.value == "INSUFFICIENT_EVIDENCE"


def test_policy_does_not_attach_dense_search_neighbours_to_general_conversation() -> None:
    citation = Citation(
        source_name="Ministry of Cooperation",
        title="Official source",
        url="https://www.cooperation.gov.in/en/homepage",
        freshness_status=DocumentStatus.CURRENT,
    )
    retrieval = RetrievalResult(
        evidence=(
            RetrievedEvidence(
                chunk_id="hello-neighbour",
                text="Unrelated source content",
                score=0.42,
                citation=citation,
                source_priority=100,
            ),
        )
    )

    decision = decide_response(message="Hello, how are you?", language="en-IN", retrieval=retrieval)

    assert decision.evidence_status.value == "GENERAL_MODEL_KNOWLEDGE"
    assert decision.retrieval.citations == ()


def test_policy_limits_a_grounded_answer_to_two_actual_source_links() -> None:
    def evidence(source: str, ordinal: int) -> RetrievedEvidence:
        return RetrievedEvidence(
            chunk_id=f"chunk-{ordinal}",
            text=f"Verified content {ordinal}",
            score=0.9 - ordinal / 100,
            citation=Citation(
                source_name=source,
                title=f"{source} document",
                url=f"https://pmfby.gov.in/notification/{ordinal}.pdf",
                freshness_status=DocumentStatus.CURRENT,
            ),
            source_priority=100,
        )

    decision = decide_response(
        message="What is the current PMFBY scheme procedure?",
        language="en-IN",
        retrieval=RetrievalResult(evidence=tuple(evidence(f"Source {ordinal}", ordinal) for ordinal in range(5))),
    )

    assert len(decision.retrieval.citations) == 2
    assert len(decision.retrieval.evidence) == 2


def test_registry_sync_preserves_failed_source_operational_state() -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(AuthBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            repository = KnowledgeRepository(session)
            await repository.sync_source_registry()
            source = await session.get(KnowledgeSource, "pmfby")
            assert source is not None
            source.validation_status = SourceValidationStatus.CHECK_FAILED.value
            source.last_successful_check_at = datetime.now(UTC)
            await session.commit()
            await repository.sync_source_registry()
            await session.refresh(source)
            assert source.validation_status == SourceValidationStatus.CHECK_FAILED.value
            assert "pmfby" in {item.key for item in await repository.due_sources()}
        await engine.dispose()

    asyncio.run(scenario())


def test_document_versions_preserve_history_and_only_one_current_version() -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(AuthBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            repository = KnowledgeRepository(session)
            await repository.sync_source_registry()
            first, created_first = await repository.record_document_version(
                source_key="pmfby",
                canonical_url="https://pmfby.gov.in/guidelines",
                source_url="https://pmfby.gov.in/guidelines",
                title="PMFBY Guidelines",
                content_hash="a" * 64,
                extraction_method="html",
                is_ocr=False,
                ocr_confidence=None,
                source_metadata={},
            )
            await session.commit()
            unchanged, created_unchanged = await repository.record_document_version(
                source_key="pmfby",
                canonical_url="https://pmfby.gov.in/guidelines",
                source_url="https://pmfby.gov.in/guidelines",
                title="PMFBY Guidelines",
                content_hash="a" * 64,
                extraction_method="html",
                is_ocr=False,
                ocr_confidence=None,
                source_metadata={},
            )
            await session.commit()
            second, created_second = await repository.record_document_version(
                source_key="pmfby",
                canonical_url="https://pmfby.gov.in/guidelines",
                source_url="https://pmfby.gov.in/guidelines",
                title="PMFBY Guidelines",
                content_hash="b" * 64,
                extraction_method="html",
                is_ocr=False,
                ocr_confidence=None,
                source_metadata={},
            )
            await session.commit()
            await session.refresh(first)
            await session.refresh(second)
            assert created_first and created_second
            assert not created_unchanged
            assert unchanged.id == first.id
            assert first.status == DocumentStatus.SUPERSEDED.value
            assert second.status == DocumentStatus.CURRENT.value
            assert second.version_number == first.version_number + 1
        await engine.dispose()

    asyncio.run(scenario())


def test_coverage_and_failed_resource_state_are_auditable_independently() -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(AuthBase.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            repository = KnowledgeRepository(session)
            await repository.sync_source_registry()
            source = SOURCES_BY_KEY["pmfby"]
            version, changed = await repository.record_document_version(
                source_key=source.key,
                canonical_url="https://pmfby.gov.in/faq",
                source_url="https://pmfby.gov.in/faq",
                title="PMFBY FAQ",
                content_hash="c" * 64,
                extraction_method="html",
                is_ocr=False,
                ocr_confidence=None,
                source_metadata={},
                coverage_categories=source.expected_categories,
            )
            assert changed
            await repository.add_chunks(
                document_version_id=version.id,
                chunks=[{"content": "Verified PMFBY FAQ content.", "content_hash": "d" * 64}],
            )
            await session.commit()
            await repository.record_resource_failure(
                source_key=source.key,
                canonical_url="https://pmfby.gov.in/pdf/unavailable.pdf",
                failure_code="source_fetch_failed",
            )
            snapshot = await repository.admin_dashboard_snapshot()
            row = next(item for item in snapshot["sources"] if item["key"] == source.key)
            assert row["coverage_state"] == "COMPLETE"
            assert row["failed_resource_count"] == 1
            await repository.resolve_resource_failure(
                source_key=source.key,
                canonical_url="https://pmfby.gov.in/pdf/unavailable.pdf",
            )
            resolved = await repository.admin_dashboard_snapshot()
            resolved_row = next(item for item in resolved["sources"] if item["key"] == source.key)
            assert resolved_row["failed_resource_count"] == 0
        await engine.dispose()

    asyncio.run(scenario())
