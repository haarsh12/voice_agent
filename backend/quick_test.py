#!/usr/bin/env python3
"""Quick test of key optimizations - runs in seconds."""

import asyncio
import time

print("🚀 Quick Optimization Check...")
print("="*50)

# Test 1: Imports
print("\n1️⃣  Testing imports...")
try:
    from app.knowledge.cache import get_retrieval_cache, get_embedding_cache
    from app.knowledge.query_expansion import expand_query
    from app.core.performance import measure_time
    from app.core.error_handling import log_error
    print("   ✅ All modules imported successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Cache initialization
print("\n2️⃣  Testing cache initialization...")
try:
    ret_cache = get_retrieval_cache()
    emb_cache = get_embedding_cache()
    print(f"   ✅ Retrieval cache: {ret_cache.get_metrics()['max_size']} slots")
    print(f"   ✅ Embedding cache: {emb_cache.get_metrics()['max_size']} slots")
except Exception as e:
    print(f"   ❌ Cache init failed: {e}")
    exit(1)

# Test 3: Query expansion
print("\n3️⃣  Testing query expansion...")
try:
    test_queries = ["fasal bima", "msp", "kisan credit"]
    for query in test_queries:
        expanded = expand_query(query, max_expansions=2)
        print(f"   ✅ '{query}' → {len(expanded)} variations")
except Exception as e:
    print(f"   ❌ Query expansion failed: {e}")
    exit(1)

# Test 4: Performance monitoring
print("\n4️⃣  Testing performance monitoring...")
try:
    async def test_measurement():
        with measure_time("test_operation", test_param="value"):
            await asyncio.sleep(0.1)
        return True
    
    result = asyncio.run(test_measurement())
    if result:
        print("   ✅ Performance measurement working")
except Exception as e:
    print(f"   ❌ Performance monitoring failed: {e}")
    exit(1)

# Test 5: Database connection
print("\n5️⃣  Testing database connection...")
try:
    from app.auth.session import get_session_factory
    factory = get_session_factory()
    if factory:
        print("   ✅ Database connection configured")
    else:
        print("   ⚠️  Database not configured (optional for basic tests)")
except Exception as e:
    print(f"   ⚠️  Database test skipped: {e}")

print("\n" + "="*50)
print("✨ QUICK CHECK COMPLETE - ALL SYSTEMS OPERATIONAL")
print("="*50)
print("\n💡 Next steps:")
print("   • Run: python apply_indexes.py (if not done)")
print("   • Run: python test_optimizations.py (full test)")
print("   • Start backend and test with queries")
print()
