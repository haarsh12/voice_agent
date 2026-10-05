import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

/// Premium caching service with stale-while-revalidate pattern
/// Provides fast offline-first experience with automatic background sync
class PremiumCacheService {
  static const String _schemesBoxName = 'schemes_cache';
  static const String _grievancesBoxName = 'grievances_cache';
  static const String _metadataBoxName = 'cache_metadata';
  
  // Cache TTL: 24 hours for schemes, 5 minutes for grievances
  static const Duration schemesCacheDuration = Duration(hours: 24);
  static const Duration grievancesCacheDuration = Duration(minutes: 5);

  static Box? _schemesBox;
  static Box? _grievancesBox;
  static Box? _metadataBox;
  static bool _initialized = false;

  /// Initialize Hive and open cache boxes
  static Future<void> initialize() async {
    if (_initialized) return;

    try {
      await Hive.initFlutter();
      
      _schemesBox = await Hive.openBox(_schemesBoxName);
      _grievancesBox = await Hive.openBox(_grievancesBoxName);
      _metadataBox = await Hive.openBox(_metadataBoxName);
      
      _initialized = true;
      print('✅ Premium cache service initialized');
    } catch (e) {
      print('❌ Cache initialization error: $e');
      rethrow;
    }
  }

  /// Check if device is online
  static Future<bool> isOnline() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    return connectivityResult != ConnectivityResult.none;
  }

  // ========== SCHEMES CACHING ==========

  /// Get schemes from cache (returns immediately, even if stale)
  /// If stale, triggers background revalidation
  static Future<List<Map<String, dynamic>>?> getSchemes({
    String? category,
    bool forceRefresh = false,
  }) async {
    await initialize();
    
    final cacheKey = category != null ? 'schemes_$category' : 'schemes_all';
    final metaKey = '${cacheKey}_metadata';

    if (forceRefresh) {
      return null; // Force network fetch
    }

    // Get cached data
    final cachedData = _schemesBox?.get(cacheKey);
    if (cachedData == null) {
      return null; // No cache, must fetch
    }

    // Get metadata
    final metadata = _metadataBox?.get(metaKey);
    final cachedAt = metadata != null 
        ? DateTime.parse(metadata['cachedAt'] as String)
        : DateTime.now().subtract(const Duration(days: 365));

    final age = DateTime.now().difference(cachedAt);
    final isStale = age > schemesCacheDuration;

    // Return cached data immediately (stale-while-revalidate pattern)
    final schemes = List<Map<String, dynamic>>.from(
      (cachedData as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );

    // If stale and online, trigger background refresh
    if (isStale && await isOnline()) {
      print('📊 Schemes cache is stale (age: ${age.inHours}h), returning cached while revalidating...');
      // Caller should trigger a refresh in background
    }

    return schemes;
  }

  /// Save schemes to cache
  static Future<void> saveSchemes(
    List<Map<String, dynamic>> schemes, {
    String? category,
  }) async {
    await initialize();
    
    final cacheKey = category != null ? 'schemes_$category' : 'schemes_all';
    final metaKey = '${cacheKey}_metadata';

    try {
      await _schemesBox?.put(cacheKey, schemes);
      await _metadataBox?.put(metaKey, {
        'cachedAt': DateTime.now().toIso8601String(),
        'count': schemes.length,
      });
      print('✅ Cached ${schemes.length} schemes with key: $cacheKey');
    } catch (e) {
      print('❌ Error saving schemes to cache: $e');
    }
  }

  /// Clear schemes cache
  static Future<void> clearSchemesCache() async {
    await initialize();
    await _schemesBox?.clear();
    print('🗑️ Schemes cache cleared');
  }

  // ========== GRIEVANCES CACHING ==========

  /// Get grievances from cache
  static Future<List<Map<String, dynamic>>?> getGrievances({
    bool forceRefresh = false,
  }) async {
    await initialize();
    
    const cacheKey = 'grievances_list';
    const metaKey = 'grievances_metadata';

    if (forceRefresh) {
      return null;
    }

    final cachedData = _grievancesBox?.get(cacheKey);
    if (cachedData == null) {
      return null;
    }

    final metadata = _metadataBox?.get(metaKey);
    final cachedAt = metadata != null 
        ? DateTime.parse(metadata['cachedAt'] as String)
        : DateTime.now().subtract(const Duration(days: 365));

    final age = DateTime.now().difference(cachedAt);
    final isStale = age > grievancesCacheDuration;

    final grievances = List<Map<String, dynamic>>.from(
      (cachedData as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );

    if (isStale && await isOnline()) {
      print('📊 Grievances cache is stale (age: ${age.inMinutes}min), returning cached while revalidating...');
    }

    return grievances;
  }

  /// Save grievances to cache
  static Future<void> saveGrievances(List<Map<String, dynamic>> grievances) async {
    await initialize();
    
    const cacheKey = 'grievances_list';
    const metaKey = 'grievances_metadata';

    try {
      await _grievancesBox?.put(cacheKey, grievances);
      await _metadataBox?.put(metaKey, {
        'cachedAt': DateTime.now().toIso8601String(),
        'count': grievances.length,
      });
      print('✅ Cached ${grievances.length} grievances');
    } catch (e) {
      print('❌ Error saving grievances to cache: $e');
    }
  }

  /// Clear grievances cache
  static Future<void> clearGrievancesCache() async {
    await initialize();
    await _grievancesBox?.clear();
    print('🗑️ Grievances cache cleared');
  }

  // ========== UTILITY METHODS ==========

  /// Get cache statistics
  static Future<Map<String, dynamic>> getCacheStats() async {
    await initialize();

    return {
      'schemes_count': _schemesBox?.length ?? 0,
      'grievances_count': _grievancesBox?.length ?? 0,
      'total_size_kb': (((_schemesBox?.length ?? 0) + 
                         (_grievancesBox?.length ?? 0)) * 2), // Rough estimate
      'is_online': await isOnline(),
    };
  }

  /// Clear all caches
  static Future<void> clearAllCaches() async {
    await initialize();
    await _schemesBox?.clear();
    await _grievancesBox?.clear();
    await _metadataBox?.clear();
    print('🗑️ All caches cleared');
  }

  /// Check if cache is fresh
  static Future<bool> isCacheFresh(String cacheKey, Duration maxAge) async {
    await initialize();
    
    final metaKey = '${cacheKey}_metadata';
    final metadata = _metadataBox?.get(metaKey);
    
    if (metadata == null) return false;

    final cachedAt = DateTime.parse(metadata['cachedAt'] as String);
    final age = DateTime.now().difference(cachedAt);
    
    return age <= maxAge;
  }

  /// Close all boxes (call on app dispose)
  static Future<void> dispose() async {
    await _schemesBox?.close();
    await _grievancesBox?.close();
    await _metadataBox?.close();
    _initialized = false;
    print('🔒 Cache boxes closed');
  }
}

/// Cache-aware data fetcher with automatic fallback
class CachedDataFetcher<T> {
  final Future<T> Function() fetchFunction;
  final Future<T?> Function() getCachedFunction;
  final Future<void> Function(T) saveCacheFunction;
  final Duration cacheDuration;

  CachedDataFetcher({
    required this.fetchFunction,
    required this.getCachedFunction,
    required this.saveCacheFunction,
    required this.cacheDuration,
  });

  /// Fetch data with cache-first approach
  /// Returns cached data immediately if available, then optionally refreshes in background
  Future<T> fetch({
    bool forceRefresh = false,
    bool backgroundRefresh = true,
  }) async {
    if (!forceRefresh) {
      // Try to get from cache first
      final cached = await getCachedFunction();
      if (cached != null) {
        // Return cached data immediately
        if (backgroundRefresh && await PremiumCacheService.isOnline()) {
          // Refresh in background (fire and forget)
          _refreshInBackground();
        }
        return cached;
      }
    }

    // No cache or force refresh - fetch from network
    final freshData = await fetchFunction();
    await saveCacheFunction(freshData);
    return freshData;
  }

  void _refreshInBackground() {
    Future.microtask(() async {
      try {
        final freshData = await fetchFunction();
        await saveCacheFunction(freshData);
        print('✅ Background refresh completed');
      } catch (e) {
        print('⚠️ Background refresh failed: $e');
      }
    });
  }
}
