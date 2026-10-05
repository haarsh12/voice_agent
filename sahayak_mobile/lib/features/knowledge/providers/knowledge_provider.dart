import 'package:flutter/material.dart';
import '../../../core/services/api_client.dart';
import '../../../core/services/cache_service.dart';
import '../models/knowledge_document.dart';

class KnowledgeProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  final CacheService _cache = CacheService();

  Map<String, dynamic>? _knowledgeBase;
  List<KnowledgeDocument> _documents = [];
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;

  // Pagination
  int _currentPage = 1;
  final int _pageSize = 15;
  bool _hasMore = true;

  Map<String, dynamic>? get knowledgeBase => _knowledgeBase;
  List<KnowledgeDocument> get documents => _documents;
  bool get isLoading => _isLoading;
  bool get isLoadingMore => _isLoadingMore;
  String? get errorMessage => _errorMessage;
  bool get hasMore => _hasMore;

  Future<void> fetchKnowledgeBase({bool forceRefresh = false}) async {
    if (!forceRefresh) {
      final cached = await _cache.getCachedKnowledge();
      if (cached != null) {
        _knowledgeBase = cached;
        notifyListeners();
        return;
      }
    }

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _api.get('/api/knowledge');
      _knowledgeBase = response;

      await _cache.cacheKnowledge(response);

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load knowledge base: $e';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchDocuments({bool forceRefresh = false}) async {
    if (_isLoading || _isLoadingMore) return;

    if (forceRefresh) {
      _currentPage = 1;
      _documents.clear();
      _hasMore = true;
    }

    _isLoading = _currentPage == 1;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _api.get(
        '/api/knowledge/documents',
        queryParams: {
          'page': _currentPage.toString(),
          'limit': _pageSize.toString(),
        },
      );

      final List<dynamic> data = response['documents'] ?? [];
      final newDocs = data.map((e) => KnowledgeDocument.fromJson(e)).toList();

      if (_currentPage == 1) {
        _documents = newDocs;
      } else {
        _documents.addAll(newDocs);
      }

      _hasMore = newDocs.length >= _pageSize;

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _errorMessage = 'Failed to load documents: $e';
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadMoreDocuments() async {
    if (!_hasMore || _isLoadingMore || _isLoading) return;

    _isLoadingMore = true;
    notifyListeners();

    try {
      _currentPage++;

      final response = await _api.get(
        '/api/knowledge/documents',
        queryParams: {
          'page': _currentPage.toString(),
          'limit': _pageSize.toString(),
        },
      );

      final List<dynamic> data = response['documents'] ?? [];
      final newDocs = data.map((e) => KnowledgeDocument.fromJson(e)).toList();

      _documents.addAll(newDocs);
      _hasMore = newDocs.length >= _pageSize;

      _isLoadingMore = false;
      notifyListeners();
    } catch (e) {
      _currentPage--;
      _isLoadingMore = false;
      notifyListeners();
    }
  }
}
