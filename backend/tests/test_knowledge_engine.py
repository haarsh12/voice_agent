"""Focused coverage for the source-grounded knowledge-engine safeguards."""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthBase
from app.knowledge.chunking import chunk_semantically
from app.knowledge.contracts import DocumentStatus, RetrievalResult, SourceValidationStatus
from app.knowledge.models import KnowledgeSource
from app.knowledge.policy import decide_response
from app.knowledge.registry import SOURCE_REGISTRY, SOURCES_BY_KEY, is_approved_source_url
from app.knowledge.repository import KnowledgeRepository


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


def test_registry_rejects_userinfo_http_and_unapproved_redirect_targets() -> None:
    source = SOURCES_BY_KEY["pmfby"]
    assert is_approved_source_url("https://pmfby.gov.in/", source)
    assert not is_approved_source_url("http://pmfby.gov.in/", source)
    assert not is_approved_source_url("https://pmfby.gov.in@attacker.example/", source)
    assert not is_approved_source_url("https://attacker.example/pmfby.gov.in", source)


def test_semantic_chunking_keeps_heading_with_its_related_paragraphs() -> None:
    chunks = chunk_semantically(
        "ELIGIBILITY\n\nFarmers must check the current official notification.\n\n"
        "CLAIM PROCESS\n\nKeep the acknowledgement and follow the applicable instructions."
    )

    assert len(chunks) == 2
    assert chunks[0].heading == "ELIGIBILITY"
    assert "Farmers" in chunks[0].content
    assert chunks[1].heading == "CLAIM PROCESS"


def test_policy_abstains_on_an_unverified_current_scheme_question() -> None:
    decision = decide_response(
        message="What is the current PMFBY claim procedure and deadline?",
        language="en-IN",
        retrieval=RetrievalResult(),
    )

    assert decision.requires_abstention is True
    assert decision.evidence_status.value == "INSUFFICIENT_EVIDENCE"
    assert decision.abstention_message and "could not verify" in decision.abstention_message.casefold()


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
            await session.commit()
            await repository.sync_source_registry()
            await session.refresh(source)
            assert source.validation_status == SourceValidationStatus.CHECK_FAILED.value
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
