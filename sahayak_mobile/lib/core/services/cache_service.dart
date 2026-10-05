import 'package:hive_flutter/hive_flutter.dart';
import 'package:logger/logger.dart';

/// Cache service for storing app data locally
/// Uses Hive for fast, encrypted local storage
class CacheService {
  static final Logger _logger = Logger(printer: PrettyPrinter(methodCount: 0));

  static const String _schemesBox = 'schemes_cache';
  static const String _servicesBox = 'services_cache';
  static const String _knowledgeBox = 'knowledge_cache';
  static const String _grievancesBox = 'grievances_cache';
  static const String _userBox = 'user_cache';

  /// Initialize Hive and open boxes
  static Future<void> initialize() async {
    try {
      await Hive.initFlutter();
      _logger.d('Hive initialized');
    } catch (e) {
      _logger.e('Failed to initialize Hive: $e');
      rethrow;
    }
  }

  /// Get box with automatic opening
  Future<Box> _getBox(String boxName) async {
    if (!Hive.isBoxOpen(boxName)) {
      return await Hive.openBox(boxName);
    }
    return Hive.box(boxName);
  }

  // ===== SCHEMES CACHE =====

  /// Cache schemes data
  Future<void> cacheSchemes(List<Map<String, dynamic>> schemes) async {
    try {
      final box = await _getBox(_schemesBox);
      await box.put('schemes_list', schemes);
      await box.put('schemes_last_updated', DateTime.now().toIso8601String());
      _logger.d('Cached ${schemes.length} schemes');
    } catch (e) {
      _logger.e('Failed to cache schemes: $e');
    }
  }

  /// Get cached schemes
  Future<List<Map<String, dynamic>>?> getCachedSchemes() async {
    try {
      final box = await _getBox(_schemesBox);
      final data = box.get('schemes_list');
      if (data != null) {
        return List<Map<String, dynamic>>.from(data);
      }
    } catch (e) {
      _logger.e('Failed to get cached schemes: $e');
    }
    return null;
  }

  /// Check if schemes cache is fresh (within 24 hours)
  Future<bool> isSchemeCacheFresh() async {
    try {
      final box = await _getBox(_schemesBox);
      final lastUpdated = box.get('schemes_last_updated');
      if (lastUpdated != null) {
        final updateTime = DateTime.parse(lastUpdated);
        final difference = DateTime.now().difference(updateTime);
        return difference.inHours < 24;
      }
    } catch (e) {
      _logger.e('Failed to check schemes cache freshness: $e');
    }
    return false;
  }

  // ===== SERVICES CACHE =====

  /// Cache services data
  Future<void> cacheServices(List<Map<String, dynamic>> services) async {
    try {
      final box = await _getBox(_servicesBox);
      await box.put('services_list', services);
      await box.put('services_last_updated', DateTime.now().toIso8601String());
      _logger.d('Cached ${services.length} services');
    } catch (e) {
      _logger.e('Failed to cache services: $e');
    }
  }

  /// Get cached services
  Future<List<Map<String, dynamic>>?> getCachedServices() async {
    try {
      final box = await _getBox(_servicesBox);
      final data = box.get('services_list');
      if (data != null) {
        return List<Map<String, dynamic>>.from(data);
      }
    } catch (e) {
      _logger.e('Failed to get cached services: $e');
    }
    return null;
  }

  /// Check if services cache is fresh (within 24 hours)
  Future<bool> isServiceCacheFresh() async {
    try {
      final box = await _getBox(_servicesBox);
      final lastUpdated = box.get('services_last_updated');
      if (lastUpdated != null) {
        final updateTime = DateTime.parse(lastUpdated);
        final difference = DateTime.now().difference(updateTime);
        return difference.inHours < 24;
      }
    } catch (e) {
      _logger.e('Failed to check services cache freshness: $e');
    }
    return false;
  }

  // ===== KNOWLEDGE BASE CACHE =====

  /// Cache knowledge base data
  Future<void> cacheKnowledge(Map<String, dynamic> knowledge) async {
    try {
      final box = await _getBox(_knowledgeBox);
      await box.put('knowledge_data', knowledge);
      await box.put('knowledge_last_updated', DateTime.now().toIso8601String());
      _logger.d('Cached knowledge base');
    } catch (e) {
      _logger.e('Failed to cache knowledge: $e');
    }
  }

  /// Get cached knowledge base
  Future<Map<String, dynamic>?> getCachedKnowledge() async {
    try {
      final box = await _getBox(_knowledgeBox);
      final data = box.get('knowledge_data');
      if (data != null) {
        return Map<String, dynamic>.from(data);
      }
    } catch (e) {
      _logger.e('Failed to get cached knowledge: $e');
    }
    return null;
  }

  // ===== USER DATA CACHE =====

  /// Cache user profile
  Future<void> cacheUserProfile(Map<String, dynamic> profile) async {
    try {
      final box = await _getBox(_userBox);
      await box.put('user_profile', profile);
      _logger.d('Cached user profile');
    } catch (e) {
      _logger.e('Failed to cache user profile: $e');
    }
  }

  /// Get cached user profile
  Future<Map<String, dynamic>?> getCachedUserProfile() async {
    try {
      final box = await _getBox(_userBox);
      final data = box.get('user_profile');
      if (data != null) {
        return Map<String, dynamic>.from(data);
      }
    } catch (e) {
      _logger.e('Failed to get cached user profile: $e');
    }
    return null;
  }

  // ===== GENERIC CACHE OPERATIONS =====

  /// Save key-value pair in user box
  Future<void> saveValue(String key, dynamic value) async {
    try {
      final box = await _getBox(_userBox);
      await box.put(key, value);
    } catch (e) {
      _logger.e('Failed to save value: $e');
    }
  }

  /// Get value from user box
  Future<dynamic> getValue(String key) async {
    try {
      final box = await _getBox(_userBox);
      return box.get(key);
    } catch (e) {
      _logger.e('Failed to get value: $e');
      return null;
    }
  }

  // ===== GUEST MODE =====

  /// Set guest mode
  Future<void> setGuestMode(bool isGuest) async {
    try {
      final box = await _getBox(_userBox);
      await box.put('is_guest_mode', isGuest);
      _logger.d('Guest mode set to: $isGuest');
    } catch (e) {
      _logger.e('Failed to set guest mode: $e');
    }
  }

  /// Check if in guest mode
  Future<bool> isGuestMode() async {
    try {
      final box = await _getBox(_userBox);
      return box.get('is_guest_mode', defaultValue: false);
    } catch (e) {
      _logger.e('Failed to check guest mode: $e');
      return false;
    }
  }

  // ===== CLEAR OPERATIONS =====

  /// Clear all cached data
  Future<void> clearAll() async {
    try {
      await Hive.deleteBoxFromDisk(_schemesBox);
      await Hive.deleteBoxFromDisk(_servicesBox);
      await Hive.deleteBoxFromDisk(_knowledgeBox);
      await Hive.deleteBoxFromDisk(_grievancesBox);
      await Hive.deleteBoxFromDisk(_userBox);
      _logger.d('All cache cleared');
    } catch (e) {
      _logger.e('Failed to clear cache: $e');
    }
  }

  /// Clear specific box
  Future<void> clearBox(String boxName) async {
    try {
      await Hive.deleteBoxFromDisk(boxName);
      _logger.d('Box $boxName cleared');
    } catch (e) {
      _logger.e('Failed to clear box $boxName: $e');
    }
  }
}
