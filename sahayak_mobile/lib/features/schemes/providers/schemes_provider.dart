import 'package:flutter/material.dart';
import '../../../core/services/api_client.dart';
import '../../../core/services/cache_service.dart';
import '../models/scheme_model.dart';

/// Manages government schemes data with pagination support
class SchemesProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  final CacheService _cache = CacheService();

  List<SchemeModel> _schemes = [];
  List<SchemeModel> _filteredSchemes = [];
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;
  String _searchQuery = '';
  String? _selectedCategory;

  // Pagination
  int _currentPage = 1;
  final int _pageSize = 20;
  bool _hasMore = true;

  List<SchemeModel> get schemes => _filteredSchemes;
  bool get isLoading => _isLoading;
  bool get isLoadingMore => _isLoadingMore;
  String? get errorMessage => _errorMessage;
  String get searchQuery => _searchQuery;
  String? get selectedCategory => _selectedCategory;
  bool get hasMore => _hasMore;
  int get currentPage => _currentPage;

  /// Fetch schemes with pagination
  Future<void> fetchSchemes({bool forceRefresh = false}) async {
    if (_isLoading || _isLoadingMore) return;

    // Check cache first (only for initial load)
    if (!forceRefresh && _currentPage == 1) {
      final isCacheFresh = await _cache.isSchemeCacheFresh();
      if (isCacheFresh) {
        final cached = await _cache.getCachedSchemes();
        if (cached != null && cached.isNotEmpty) {
          _schemes = cached.map((e) => SchemeModel.fromJson(e)).toList();
          _filteredSchemes = _schemes;
          _hasMore = false; // Cached data is complete
          notifyListeners();
          return;
        }
      }
    }

    if (forceRefresh) {
      _currentPage = 1;
      _schemes.clear();
      _filteredSchemes.clear();
      _hasMore = true;
    }

    _isLoading = _currentPage == 1;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _api.get(
        '/api/schemes',
        queryParams: {
          'page': _currentPage.toString(),
          'limit': _pageSize.toString(),
        },
      );
      
      final List<dynamic> data = response['items'] ?? response['schemes'] ?? response ?? [];
      final newSchemes = data.map((e) => SchemeModel.fromJson(e)).toList();
      
      if (_currentPage == 1) {
        _schemes = newSchemes;
      } else {
        _schemes.addAll(newSchemes);
      }

      // Check if there are more pages — use API flag if present
      _hasMore = response['has_more'] as bool? ?? (newSchemes.length >= _pageSize);

      // Apply current filters
      _applyFilters();

      // Cache only first page
      if (_currentPage == 1) {
        await _cache.cacheSchemes(data.cast<Map<String, dynamic>>());
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load schemes: $e';
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Load next page of schemes
  Future<void> loadMoreSchemes() async {
    if (!_hasMore || _isLoadingMore || _isLoading) return;

    _isLoadingMore = true;
    notifyListeners();

    try {
      _currentPage++;
      
      final response = await _api.get(
        '/api/schemes',
        queryParams: {
          'page': _currentPage.toString(),
          'limit': _pageSize.toString(),
        },
      );
      
      final List<dynamic> data = response['items'] ?? response['schemes'] ?? response ?? [];
      final newSchemes = data.map((e) => SchemeModel.fromJson(e)).toList();
      
      _schemes.addAll(newSchemes);
      
      // Check if there are more pages
      _hasMore = newSchemes.length >= _pageSize;
      
      // Apply current filters
      _applyFilters();

      _isLoadingMore = false;
      notifyListeners();
    } catch (e) {
      // Revert page increment on error
      _currentPage--;
      _isLoadingMore = false;
      notifyListeners();
    }
  }

  /// Reset pagination
  void resetPagination() {
    _currentPage = 1;
    _hasMore = true;
    _schemes.clear();
    _filteredSchemes.clear();
  }

  /// Search schemes
  void searchSchemes(String query) {
    _searchQuery = query;
    _applyFilters();
  }

  /// Filter by category
  void filterByCategory(String? category) {
    _selectedCategory = category;
    _applyFilters();
  }

  /// Apply search and filter
  void _applyFilters() {
    _filteredSchemes = _schemes.where((scheme) {
      final matchesSearch = _searchQuery.isEmpty ||
          scheme.title.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          (scheme.description?.toLowerCase().contains(_searchQuery.toLowerCase()) ?? false);

      final matchesCategory = _selectedCategory == null ||
          scheme.category == _selectedCategory;

      return matchesSearch && matchesCategory;
    }).toList();

    notifyListeners();
  }

  /// Get scheme by ID (from already-loaded list)
  SchemeModel? getSchemeById(String id) {
    try {
      return _schemes.firstWhere((s) => s.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Fetch full scheme detail by ID from API
  Future<SchemeModel?> fetchSchemeById(String id) async {
    // Return cached version if we already have it
    final cached = getSchemeById(id);
    if (cached?.data != null) return cached;

    try {
      final response = await _api.get('/api/schemes/$id');
      return SchemeModel.fromJson(response);
    } catch (e) {
      return cached; // Fall back to cached version without detail
    }
  }

  /// Clear filters
  void clearFilters() {
    _searchQuery = '';
    _selectedCategory = null;
    _filteredSchemes = _schemes;
    notifyListeners();
  }

  List<String> get categories {
    final cats = _schemes.map((e) => e.category).where((e) => e != null).cast<String>().toSet().toList();
    cats.sort();
    return cats;
  }
}
