import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:logger/logger.dart';

/// Secure storage for authentication tokens
/// Uses platform secure storage (Keychain on iOS, EncryptedSharedPreferences on Android)
class AuthTokenStore {
  static final Logger _logger = Logger(printer: PrettyPrinter(methodCount: 0));
  
  static const String _tokenKey = 'auth_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _userIdKey = 'user_id';
  static const String _phoneKey = 'phone_number';

  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
  );

  /// Save authentication token
  Future<void> saveToken(String token) async {
    try {
      await _storage.write(key: _tokenKey, value: token);
      _logger.d('Auth token saved securely');
    } catch (e) {
      _logger.e('Failed to save auth token: $e');
      rethrow;
    }
  }

  /// Read authentication token
  Future<String?> read() async {
    try {
      return await _storage.read(key: _tokenKey);
    } catch (e) {
      _logger.e('Failed to read auth token: $e');
      return null;
    }
  }

  /// Save refresh token
  Future<void> saveRefreshToken(String token) async {
    try {
      await _storage.write(key: _refreshTokenKey, value: token);
      _logger.d('Refresh token saved securely');
    } catch (e) {
      _logger.e('Failed to save refresh token: $e');
    }
  }

  /// Read refresh token
  Future<String?> readRefreshToken() async {
    try {
      return await _storage.read(key: _refreshTokenKey);
    } catch (e) {
      _logger.e('Failed to read refresh token: $e');
      return null;
    }
  }

  /// Save user ID
  Future<void> saveUserId(String userId) async {
    try {
      await _storage.write(key: _userIdKey, value: userId);
    } catch (e) {
      _logger.e('Failed to save user ID: $e');
    }
  }

  /// Read user ID
  Future<String?> readUserId() async {
    try {
      return await _storage.read(key: _userIdKey);
    } catch (e) {
      _logger.e('Failed to read user ID: $e');
      return null;
    }
  }

  /// Save phone number
  Future<void> savePhone(String phone) async {
    try {
      await _storage.write(key: _phoneKey, value: phone);
    } catch (e) {
      _logger.e('Failed to save phone: $e');
    }
  }

  /// Read phone number
  Future<String?> readPhone() async {
    try {
      return await _storage.read(key: _phoneKey);
    } catch (e) {
      _logger.e('Failed to read phone: $e');
      return null;
    }
  }

  /// Delete authentication token
  Future<void> delete() async {
    try {
      await _storage.delete(key: _tokenKey);
      _logger.d('Auth token deleted');
    } catch (e) {
      _logger.e('Failed to delete auth token: $e');
    }
  }

  /// Clear all stored data
  Future<void> clearAll() async {
    try {
      await _storage.deleteAll();
      _logger.d('All secure data cleared');
    } catch (e) {
      _logger.e('Failed to clear secure data: $e');
    }
  }

  /// Check if user is authenticated
  Future<bool> isAuthenticated() async {
    final token = await read();
    return token != null && token.isNotEmpty;
  }
}
