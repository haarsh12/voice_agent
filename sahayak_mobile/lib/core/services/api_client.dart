import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:logger/logger.dart';

import '../config/api_config.dart';
import 'auth_token_store.dart';

/// Centralized HTTP client for all API communication
/// Handles authentication, error handling, and logging
class ApiClient {
  static final Logger _logger = Logger(
    printer: PrettyPrinter(methodCount: 0),
  );

  final AuthTokenStore _tokenStore = AuthTokenStore();
  
  String get baseUrl => ApiConfig.baseUrl;

  /// GET request
  Future<dynamic> get(
    String endpoint, {
    Map<String, String>? queryParams,
    Map<String, String>? extraHeaders,
  }) async {
    final uri = _buildUri(endpoint, queryParams);
    final headers = await _buildHeaders(extraHeaders);

    try {
      _logger.d('GET $uri');
      
      final response = await http
          .get(uri, headers: headers)
          .timeout(ApiConfig.receiveTimeout);

      return _handleResponse(response);
    } catch (e) {
      _logger.e('GET $endpoint failed: $e');
      throw _handleError(e);
    }
  }

  /// POST request
  Future<dynamic> post(
    String endpoint,
    Map<String, dynamic> data, {
    Map<String, String>? extraHeaders,
  }) async {
    final uri = _buildUri(endpoint);
    final headers = await _buildHeaders(extraHeaders);

    try {
      _logger.d('POST $uri');
      _logger.d('Body: ${jsonEncode(data)}');

      final response = await http
          .post(
            uri,
            headers: headers,
            body: jsonEncode(data),
          )
          .timeout(ApiConfig.receiveTimeout);

      return _handleResponse(response);
    } catch (e) {
      _logger.e('POST $endpoint failed: $e');
      throw _handleError(e);
    }
  }

  /// PUT request
  Future<dynamic> put(
    String endpoint,
    Map<String, dynamic> data, {
    Map<String, String>? extraHeaders,
  }) async {
    final uri = _buildUri(endpoint);
    final headers = await _buildHeaders(extraHeaders);

    try {
      _logger.d('PUT $uri');
      _logger.d('Body: ${jsonEncode(data)}');

      final response = await http
          .put(
            uri,
            headers: headers,
            body: jsonEncode(data),
          )
          .timeout(ApiConfig.receiveTimeout);

      return _handleResponse(response);
    } catch (e) {
      _logger.e('PUT $endpoint failed: $e');
      throw _handleError(e);
    }
  }

  /// DELETE request
  Future<dynamic> delete(
    String endpoint, {
    Map<String, String>? extraHeaders,
  }) async {
    final uri = _buildUri(endpoint);
    final headers = await _buildHeaders(extraHeaders);

    try {
      _logger.d('DELETE $uri');

      final response = await http
          .delete(uri, headers: headers)
          .timeout(ApiConfig.receiveTimeout);

      return _handleResponse(response);
    } catch (e) {
      _logger.e('DELETE $endpoint failed: $e');
      throw _handleError(e);
    }
  }

  /// Build URI with query parameters
  Uri _buildUri(String endpoint, [Map<String, String>? queryParams]) {
    final url = '$baseUrl$endpoint';
    if (queryParams != null && queryParams.isNotEmpty) {
      return Uri.parse(url).replace(queryParameters: queryParams);
    }
    return Uri.parse(url);
  }

  /// Build headers with authentication
  Future<Map<String, String>> _buildHeaders(
    Map<String, String>? extraHeaders,
  ) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    // Add auth token if available
    final token = await _tokenStore.read();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    // Add extra headers
    if (extraHeaders != null) {
      headers.addAll(extraHeaders);
    }

    // Keep the client identity declaration consistent for all mobile API
    // calls. The server treats it only as an AI delivery/capability hint.
    headers['X-Sahayak-Device'] = ApiConfig.clientDevice;

    return headers;
  }

  /// Handle HTTP response
  dynamic _handleResponse(http.Response response) {
    _logger.d('Response: ${response.statusCode}');

    if (response.statusCode >= 200 && response.statusCode < 300) {
      // Success
      if (response.body.isEmpty) {
        return {'message': 'Success'};
      }
      
      try {
        return jsonDecode(response.body);
      } catch (e) {
        _logger.w('Failed to decode response body');
        return {'message': 'Success', 'raw': response.body};
      }
    } else if (response.statusCode == 401) {
      // Unauthorized - clear token
      _tokenStore.delete();
      throw ApiException(
        'Unauthorized. Please login again.',
        statusCode: 401,
      );
    } else if (response.statusCode == 403) {
      throw ApiException(
        'Forbidden. You do not have permission.',
        statusCode: 403,
      );
    } else if (response.statusCode == 404) {
      throw ApiException(
        'Resource not found.',
        statusCode: 404,
      );
    } else if (response.statusCode >= 500) {
      throw ApiException(
        'Server error. Please try again later.',
        statusCode: response.statusCode,
      );
    } else {
      // Other client errors
      String message = 'Request failed';
      try {
        final body = jsonDecode(response.body);
        message = body['detail'] ?? body['message'] ?? message;
      } catch (_) {
        message = response.body.isNotEmpty ? response.body : message;
      }
      
      throw ApiException(message, statusCode: response.statusCode);
    }
  }

  /// Handle errors
  Exception _handleError(dynamic error) {
    if (error is ApiException) {
      return error;
    }
    
    if (error.toString().contains('SocketException') ||
        error.toString().contains('HandshakeException')) {
      return ApiException(
        'Network error. Please check your connection.',
        statusCode: 0,
      );
    }
    
    if (error.toString().contains('TimeoutException')) {
      return ApiException(
        'Request timeout. Please try again.',
        statusCode: 0,
      );
    }
    
    return ApiException('Unexpected error: $error');
  }
}

/// Custom exception for API errors
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}
