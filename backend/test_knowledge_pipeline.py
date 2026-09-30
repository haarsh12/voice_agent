"""Quick validation script for knowledge ingestion pipeline."""

import asyncio
import sys
from typing import Any

from sqlalchemy import select, func, text
from app.auth.session import get_session_factory, get_engine, ensure_development_auth_schema
from app.config.settings import get_settings
from app.knowledge.registry import SOURCE_REGISTRY, SOURCES_BY_KEY
from app.knowledge.retrieval import KnowledgeRetriever
from app.knowledge.models import KnowledgeDocument, KnowledgeDocumentVersion, KnowledgeChunk
from app.schemes.repository import SchemeRepository


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"  {text}")


async def test_source_registry() -> bool:
    """Test Stage 1: Verify source registry."""
    print_header("Stage 1: Source Registry Verification")
    
    try:
        total_sources = len(SOURCE_REGISTRY)
        print_info(f"Total registered sources: {total_sources}")
        
        if total_sources < 27:
            print_error(f"Expected at least 27 sources, found {total_sources}")
            return False
        
        # Check critical sources
        critical_sources = [
            "ncdc", "pm_kisan", "pmfby", "ministry_of_cooperation",
            "ministry_of_fisheries", "department_animal_husbandry_dairying",
            "food_processing_ministry", "trifed"
        ]
        
        missing = [s for s in critical_sources if s not in SOURCES_BY_KEY]
        if missing:
            print_error(f"Missing critical sources: {', '.join(missing)}")
            return False
        
        print_success(f"All {total_sources} sources registered correctly")
        print_info("Critical sources present:")
        for source_key in critical_sources:
            source = SOURCES_BY_KEY[source_key]
            print_info(f"  - {source_key}: {source.name}")
        
        return True
        
    except Exception as e:
        print_error(f"Registry test failed: {e}")
        return False


async def test_database_connection() -> bool:
    """Test database connectivity and schema."""
    print_header("Stage 2: Database Connection")
    
    try:
        settings = get_settings()
        engine = get_engine()
        factory = get_session_factory()
        
        if not engine or not factory:
            print_error("Database not configured")
            return False
        
        # Ensure schema exists (for dev SQLite)
        if (
            not settings.is_production
            and settings.async_database_url
            and settings.async_database_url.startswith("sqlite")
        ):
            await ensure_development_auth_schema(engine)
        
        async with factory() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
        print_success("Database connection successful")
        return True
        
    except Exception as e:
        print_error(f"Database test failed: {e}")
        return False


async def test_ingested_content() -> bool:
    """Test ingested documents, chunks, and schemes."""
    print_header("Stage 3: Ingested Content Verification")
    
    try:
        factory = get_session_factory()
        if not factory:
            print_error("Database not available")
            return False
        
        async with factory() as session:
            # Count documents
            doc_count = await session.scalar(
                select(func.count(KnowledgeDocument.id))
            )
            
            # Count current versions
            version_count = await session.scalar(
                select(func.count(KnowledgeDocumentVersion.id))
                .where(KnowledgeDocumentVersion.status == 'CURRENT')
            )
            
            # Count chunks
            chunk_count = await session.scalar(
                select(func.count(KnowledgeChunk.id))
                .join(KnowledgeDocumentVersion)
                .where(KnowledgeDocumentVersion.status == 'CURRENT')
            )
            
            # Count schemes
            scheme_repo = SchemeRepository(session)
            scheme_result = await session.execute(
                text("SELECT COUNT(*) FROM schemes")
            )
            scheme_count = scheme_result.scalar() or 0
            
            # Count sources with documents
            source_result = await session.execute(
                text("""
                    SELECT COUNT(DISTINCT source_key) 
                    FROM knowledge_documents
                """)
            )
            sources_with_docs = source_result.scalar() or 0
            
        print_info(f"Documents: {doc_count}")
        print_info(f"Current versions: {version_count}")
        print_info(f"Chunks: {chunk_count}")
        print_info(f"Schemes: {scheme_count}")
        print_info(f"Sources with documents: {sources_with_docs}")
        
        has_content = doc_count > 0 and chunk_count > 0
        
        if not has_content:
            print_warning("No content ingested yet. Run: python -m app.knowledge.cli --ingest-all")
            return False
        
        if scheme_count == 0:
            print_warning("No schemes extracted. Run: python -m app.knowledge.cli --backfill-schemes")
        
        if chunk_count < 100:
            print_warning(f"Only {chunk_count} chunks found. Consider ingesting more sources.")
        else:
            print_success(f"Content ingestion looks healthy")
        
        return True
        
    except Exception as e:
        print_error(f"Content verification failed: {e}")
        return False


async def test_retrieval_system() -> bool:
    """Test end-to-end retrieval with sample queries."""
    print_header("Stage 4: Knowledge Retrieval Testing")
    
    test_queries = [
        ("Cooperative schemes", "yuva sahakar"),
        ("Agriculture support", "pm kisan"),
        ("Fisheries development", "pmmsy"),
        ("NCDC financing", "ncdc loan"),
    ]
    
    try:
        settings = get_settings()
        factory = get_session_factory()
        
        if not factory:
            print_error("Database not available")
            return False
        
        success_count = 0
        
        async with factory() as session:
            retriever = KnowledgeRetriever(session, settings)
            
            for label, query in test_queries:
                print_info(f"\nTesting: {label}")
                print_info(f"Query: '{query}'")
                
                try:
                    result = await retriever.retrieve(query)
                    
                    if result.unavailable_reason:
                        print_warning(f"  Retrieval unavailable: {result.unavailable_reason}")
                        continue
                    
                    evidence_count = len(result.evidence)
                    citation_count = len(result.citations)
                    
                    print_info(f"  Evidence: {evidence_count} items")
                    print_info(f"  Citations: {citation_count}")
                    
                    if citation_count > 0:
                        first_citation = result.citations[0]
                        print_info(f"  Source: {first_citation.source_name}")
                        print_info(f"  URL: {first_citation.url}")
                        success_count += 1
                    else:
                        print_warning(f"  No citations found")
                    
                except Exception as e:
                    print_warning(f"  Query failed: {e}")
        
        if success_count == 0:
            print_warning("No queries returned citations. Vector store may need setup.")
            return False
        
        print_success(f"\n{success_count}/{len(test_queries)} queries returned citations")
        return success_count >= len(test_queries) // 2  # At least 50% success
        
    except Exception as e:
        print_error(f"Retrieval test failed: {e}")
        return False


async def test_scheme_extraction() -> bool:
    """Test scheme extraction and categorization."""
    print_header("Stage 5: Scheme Extraction Validation")
    
    try:
        factory = get_session_factory()
        if not factory:
            return False
        
        async with factory() as session:
            # Query scheme categories
            result = await session.execute(
                text("""
                    SELECT 
                        category,
                        COUNT(*) as scheme_count
                    FROM schemes
                    GROUP BY category
                    ORDER BY scheme_count DESC
                """)
            )
            
            categories = result.fetchall()
            
            if not categories:
                print_warning("No schemes found. Run backfill.")
                return False
            
            print_info("Schemes by category:")
            total_schemes = 0
            for cat, count in categories:
                print_info(f"  {cat}: {count} schemes")
                total_schemes += count
            
            # Check for key categories
            expected_categories = [
                "Cooperatives", "Agriculture", "Financial inclusion",
                "Fisheries", "Livestock & Dairy"
            ]
            
            found_categories = {cat for cat, _ in categories}
            missing = [c for c in expected_categories if c not in found_categories]
            
            if missing:
                print_warning(f"Expected categories not found: {', '.join(missing)}")
                print_info("This may be normal if those sources haven't been ingested yet.")
            
            if total_schemes >= 30:
                print_success(f"Good scheme coverage: {total_schemes} total schemes")
                return True
            else:
                print_warning(f"Limited schemes: {total_schemes}. Consider ingesting more sources.")
                return total_schemes > 0
        
    except Exception as e:
        print_error(f"Scheme extraction test failed: {e}")
        return False


async def test_qdrant_connection() -> bool:
    """Test Qdrant vector store connection."""
    print_header("Stage 6: Qdrant Vector Store")
    
    try:
        import httpx
        settings = get_settings()
        
        if not settings.qdrant_url:
            print_warning("Qdrant not configured (QDRANT_URL not set)")
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.qdrant_url}/collections/{settings.qdrant_collection_name}"
            )
            
            if response.status_code == 404:
                print_warning("Qdrant collection doesn't exist yet")
                print_info("It will be created on first ingestion")
                return False
            
            if response.status_code != 200:
                print_error(f"Qdrant error: {response.status_code}")
                return False
            
            data = response.json()
            result = data.get("result", {})
            vectors_count = result.get("vectors_count", 0)
            points_count = result.get("points_count", 0)
            
            print_info(f"Vectors: {vectors_count}")
            print_info(f"Points: {points_count}")
            
            if points_count == 0:
                print_warning("No vectors in Qdrant. Run ingestion.")
                return False
            
            print_success(f"Qdrant healthy with {points_count} points")
            return True
        
    except Exception as e:
        print_warning(f"Qdrant test failed: {e}")
        print_info("Qdrant may not be running or configured")
        return False


async def run_all_tests() -> int:
    """Run all pipeline tests."""
    print(f"\n{Colors.BOLD}{'='*70}")
    print("Sahayak AI Knowledge Pipeline Validation")
    print(f"{'='*70}{Colors.END}\n")
    
    tests = [
        ("Source Registry", test_source_registry),
        ("Database Connection", test_database_connection),
        ("Ingested Content", test_ingested_content),
        ("Scheme Extraction", test_scheme_extraction),
        ("Qdrant Vector Store", test_qdrant_connection),
        ("Knowledge Retrieval", test_retrieval_system),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("\nAll tests passed! ✓")
        print_info("\nNext steps:")
        print_info("1. Test voice agent queries in the frontend")
        print_info("2. Verify citations display correctly")
        print_info("3. Schedule regular ingestion")
        return 0
    elif passed >= total // 2:
        print_warning("\nMost tests passed, but some components need attention.")
        print_info("\nRecommended actions:")
        if not results[2][1]:  # Ingested content
            print_info("- Run: python -m app.knowledge.cli --ingest-all")
        if not results[4][1]:  # Qdrant
            print_info("- Start Qdrant: docker-compose up -d qdrant")
        return 1
    else:
        print_error("\nMultiple tests failed. Review configuration.")
        print_info("\nTroubleshooting:")
        print_info("- Check .env configuration")
        print_info("- Ensure database is accessible")
        print_info("- Start required services (Qdrant, etc.)")
        print_info("- Review TESTING_KNOWLEDGE_PIPELINE.md for details")
        return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(run_all_tests()))
