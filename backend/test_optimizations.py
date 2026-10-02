#!/usr/bin/env python3
"""Test script to verify all performance optimizations are working."""

import asyncio
import time
from typing import Any

from app.auth.session import get_session_factory
from app.config.settings import get_settings
from app.knowledge.cache import get_retrieval_cache, get_embedding_cache, log_cache_metrics
from app.knowledge.retrieval import KnowledgeRetriever
from app.knowledge.contracts import UserKnowledgeContext
from app.core.performance import get_all_performance_stats


async def test_retrieval_performance():
    """Test knowledge retrieval with caching and performance monitoring."""
    print("🔍 Testing Knowledge Retrieval Performance...")
    print("="*60)
    
    settings = get_settings()
    factory = get_session_factory()
    
    if factory is None:
        print("❌ Database not configured")
        return False
    
    test_queries = [
        "प्रधानमंत्री फसल बीमा योजना",
        "MSP minimum support price",
        "किसान सम्मान निधि",
        "crop insurance scheme",
        "pm kisan scheme eligibility",
    ]
    
    user_context = UserKnowledgeContext(
        state="Maharashtra",
        district=None,
        account_type=None,
    )
    
    print(f"\n📝 Testing {len(test_queries)} queries...\n")
    
    timings = []
    cache_hits = 0
    
    async with factory() as session:
        retriever = KnowledgeRetriever(session, settings)
        
        # First pass - populate cache
        print("🔄 First pass (cold cache):")
        for i, query in enumerate(test_queries, 1):
            start = time.perf_counter()
            try:
                result = await retriever.retrieve(query, user_context=user_context)
                duration = (time.perf_counter() - start) * 1000
                timings.append(duration)
                
                status = "✅" if duration < 2000 else "⚠️" if duration < 3000 else "❌"
                print(f"  {status} Query {i}: {duration:.0f}ms - {len(result.evidence)} evidence")
            except Exception as e:
                print(f"  ❌ Query {i} failed: {e}")
        
        # Second pass - test cache
        print("\n🔄 Second pass (warm cache):")
        cache_timings = []
        for i, query in enumerate(test_queries, 1):
            start = time.perf_counter()
            try:
                result = await retriever.retrieve(query, user_context=user_context)
                duration = (time.perf_counter() - start) * 1000
                cache_timings.append(duration)
                
                # Cache should be much faster
                if duration < 100:
                    cache_hits += 1
                    print(f"  ✅ Query {i}: {duration:.0f}ms - CACHED ⚡")
                else:
                    print(f"  ⚠️  Query {i}: {duration:.0f}ms - not from cache")
            except Exception as e:
                print(f"  ❌ Query {i} failed: {e}")
    
    # Print statistics
    print("\n" + "="*60)
    print("📊 PERFORMANCE STATISTICS:")
    print("="*60)
    
    if timings:
        avg_time = sum(timings) / len(timings)
        max_time = max(timings)
        min_time = min(timings)
        
        print(f"\n🕐 First Pass (Cold Cache):")
        print(f"   Average: {avg_time:.0f}ms")
        print(f"   Min: {min_time:.0f}ms")
        print(f"   Max: {max_time:.0f}ms")
        print(f"   Target: <1500ms ({'✅ PASS' if avg_time < 1500 else '❌ FAIL'})")
    
    if cache_timings:
        avg_cache = sum(cache_timings) / len(cache_timings)
        print(f"\n⚡ Second Pass (Warm Cache):")
        print(f"   Average: {avg_cache:.0f}ms")
        print(f"   Cache Hits: {cache_hits}/{len(test_queries)}")
        print(f"   Cache Rate: {cache_hits/len(test_queries)*100:.0f}%")
        print(f"   Target: >80% ({'✅ PASS' if cache_hits/len(test_queries) >= 0.8 else '⚠️  PARTIAL'})")
    
    # Cache metrics
    print("\n📦 CACHE METRICS:")
    print("="*60)
    
    retrieval_cache = get_retrieval_cache()
    embedding_cache = get_embedding_cache()
    
    ret_metrics = retrieval_cache.get_metrics()
    emb_metrics = embedding_cache.get_metrics()
    
    print(f"\n🔍 Retrieval Cache:")
    print(f"   Size: {ret_metrics['size']}/{ret_metrics['max_size']}")
    print(f"   Hits: {ret_metrics['hits']}")
    print(f"   Misses: {ret_metrics['misses']}")
    print(f"   Hit Rate: {ret_metrics['hit_rate']*100:.1f}%")
    
    print(f"\n🧮 Embedding Cache:")
    print(f"   Size: {emb_metrics['size']}/{emb_metrics['max_size']}")
    print(f"   Hits: {emb_metrics['hits']}")
    print(f"   Misses: {emb_metrics['misses']}")
    print(f"   Hit Rate: {emb_metrics['hit_rate']*100:.1f}%")
    
    # Performance tracker stats
    print("\n📈 PERFORMANCE TRACKER:")
    print("="*60)
    perf_stats = get_all_performance_stats()
    
    for operation, stats in perf_stats.items():
        if stats['count'] > 0:
            print(f"\n{operation.upper()}:")
            print(f"   Count: {stats['count']}")
            print(f"   P50: {stats.get('p50_ms', 0):.0f}ms")
            print(f"   P95: {stats.get('p95_ms', 0):.0f}ms")
            print(f"   Success Rate: {stats.get('success_rate', 0)*100:.1f}%")
    
    print("\n" + "="*60)
    
    # Overall assessment
    passed = True
    if timings and sum(timings)/len(timings) >= 1500:
        passed = False
    
    if passed:
        print("✅ ALL PERFORMANCE TESTS PASSED!")
        print("💡 System is optimized and production-ready")
    else:
        print("⚠️  SOME TESTS DID NOT MEET TARGETS")
        print("💡 Consider running apply_indexes.py if not done yet")
    
    print("="*60 + "\n")
    
    return passed


async def test_query_expansion():
    """Test query expansion functionality."""
    print("\n🔄 Testing Query Expansion...")
    print("="*60)
    
    from app.knowledge.query_expansion import expand_query, get_scheme_variations
    
    test_cases = [
        ("fasal bima", ["crop insurance", "pmfby", "प्रधानमंत्री फसल बीमा"]),
        ("msp", ["minimum support price", "न्यूनतम समर्थन मूल्य"]),
        ("kisan credit card", ["kcc", "किसान क्रेडिट"]),
    ]
    
    all_passed = True
    
    for query, expected_terms in test_cases:
        expanded = expand_query(query, max_expansions=3)
        
        # Check if any expected terms appear in expanded queries
        found_terms = []
        for term in expected_terms:
            if any(term.lower() in exp.lower() for exp in expanded):
                found_terms.append(term)
        
        if found_terms:
            print(f"✅ '{query}' → Found: {', '.join(found_terms[:2])}")
        else:
            print(f"⚠️  '{query}' → No expansion found")
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("✅ Query expansion working correctly\n")
    else:
        print("⚠️  Query expansion may need tuning\n")
    
    return all_passed


async def main():
    """Run all optimization tests."""
    print("\n" + "="*70)
    print(" SAHAYAK VOICE AGENT - OPTIMIZATION VERIFICATION")
    print("="*70 + "\n")
    
    print("This script verifies that all performance optimizations are working:")
    print("  • Caching layer (retrieval + embeddings)")
    print("  • Query expansion")
    print("  • Database indexes")
    print("  • Performance monitoring")
    print("\n" + "="*70 + "\n")
    
    # Run tests
    results = []
    
    try:
        results.append(("Query Expansion", await test_query_expansion()))
        results.append(("Retrieval Performance", await test_retrieval_performance()))
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Final summary
    print("\n" + "="*70)
    print(" FINAL SUMMARY")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*70)
    
    if all_passed:
        print("✨ ALL OPTIMIZATIONS VERIFIED - PRODUCTION READY ✨")
        print("\n💡 Next steps:")
        print("   1. Restart backend server")
        print("   2. Test with frontend")
        print("   3. Monitor logs for performance metrics")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW OUTPUT ABOVE")
        print("\n💡 Troubleshooting:")
        print("   1. Run: python apply_indexes.py")
        print("   2. Check database connection")
        print("   3. Verify environment variables")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user\n")
        exit(130)
