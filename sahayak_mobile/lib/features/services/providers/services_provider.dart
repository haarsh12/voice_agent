import 'package:flutter/material.dart';
import '../../../core/services/api_client.dart';
import '../../../core/services/cache_service.dart';
import '../models/service_model.dart';

/// Manages services data with pagination support
class ServicesProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  final CacheService _cache = CacheService();

  List<ServiceModel> _services = [];
  List<ServiceModel> _filteredServices = [];
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;
  String _searchQuery = '';

  // Pagination
  int _currentPage = 1;
  final int _pageSize = 20;
  bool _hasMore = true;

  List<ServiceModel> get services => _filteredServices;
  bool get isLoading => _isLoading;
  bool get isLoadingMore => _isLoadingMore;
  String? get errorMessage => _errorMessage;
  bool get hasMore => _hasMore;
  String get searchQuery => _searchQuery;

  Future<void> fetchServices({bool forceRefresh = false}) async {
    if (_isLoading || _isLoadingMore) return;

    // Check cache first (only for initial load)
    if (!forceRefresh && _currentPage == 1) {
      final isCacheFresh = await _cache.isServiceCacheFresh();
      if (isCacheFresh) {
        final cached = await _cache.getCachedServices();
        if (cached != null && cached.isNotEmpty) {
          _services = cached.map((e) => ServiceModel.fromJson(e)).toList();
          _applySearch();
          _hasMore = false;
          notifyListeners();
          return;
        }
      }
    }

    if (forceRefresh) {
      _currentPage = 1;
      _services.clear();
      _filteredServices.clear();
      _hasMore = true;
    }

    _isLoading = _currentPage == 1;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _api.get(
        '/api/services',
        queryParams: {
          'page': _currentPage.toString(),
          'limit': _pageSize.toString(),
        },
      );
      
      final List<dynamic> data = response['services'] ?? response ?? [];
      final newServices = data.map((e) => ServiceModel.fromJson(e)).toList();
      
      if (_currentPage == 1) {
        _services = newServices;
      } else {
        _services.addAll(newServices);
      }

      _hasMore = newServices.length >= _pageSize;
      _applySearch();

      // Cache only first page
      if (_currentPage == 1) {
        await _cache.cacheServices(data.cast<Map<String, dynamic>>());
      }

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load services: $e';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadMoreServices() async {
    if (!_hasMore || _isLoadingMore || _isLoading) return;

    _isLoadingMore = true;
    notifyListeners();

    try {
      _currentPage++;
      
      final response = await _api.get(
        '/api/services',
        queryParams: {
          'page': _currentPage.toString(),
          'limit': _pageSize.toString(),
        },
      );
      
      final List<dynamic> data = response['services'] ?? response ?? [];
      final newServices = data.map((e) => ServiceModel.fromJson(e)).toList();
      
      _services.addAll(newServices);
      _hasMore = newServices.length >= _pageSize;
      _applySearch();

      _isLoadingMore = false;
      notifyListeners();
    } catch (e) {
      _currentPage--;
      _isLoadingMore = false;
      notifyListeners();
    }
  }

  void searchServices(String query) {
    _searchQuery = query;
    _applySearch();
  }

  void _applySearch() {
    if (_searchQuery.isEmpty) {
      _filteredServices = _services;
    } else {
      _filteredServices = _services.where((service) =>
          service.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          (service.description?.toLowerCase().contains(_searchQuery.toLowerCase()) ?? false)).toList();
    }
    notifyListeners();
  }

  ServiceModel? getServiceById(String id) {
    try {
      return _services.firstWhere((s) => s.id == id);
    } catch (e) {
      return null;
    }
  }
}
