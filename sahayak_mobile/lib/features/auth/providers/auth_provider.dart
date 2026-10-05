import 'package:flutter/material.dart';
import '../../../core/config/api_config.dart';
import '../../../core/services/api_client.dart';
import '../../../core/services/auth_token_store.dart';
import '../../../core/services/cache_service.dart';
import '../models/user_model.dart';

enum AuthStatus {
  initial,
  authenticated,
  guest, // Guest mode - no login required
  unauthenticated,
  loading,
}

/// Manages authentication state and user session
class AuthProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  final AuthTokenStore _tokenStore = AuthTokenStore();
  final CacheService _cache = CacheService();

  AuthStatus _status = AuthStatus.initial;
  UserModel? _user;
  String? _errorMessage;
  bool _isLoading = false;

  AuthStatus get status => _status;
  UserModel? get user => _user;
  String? get errorMessage => _errorMessage;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isGuest => _status == AuthStatus.guest;

  /// Initialize auth state - check if user is already logged in or in guest mode
  Future<void> initialize() async {
    _setLoading(true);

    try {
      // Check if user chose guest mode
      final isGuestMode = await _cache.isGuestMode();

      if (isGuestMode) {
        _status = AuthStatus.guest;
        _setLoading(false);
        return;
      }

      final isAuth = await _tokenStore.isAuthenticated();

      if (isAuth) {
        // Try to load cached user profile
        final cachedProfile = await _cache.getCachedUserProfile();

        if (cachedProfile != null) {
          _user = UserModel.fromJson(cachedProfile);
          _status = AuthStatus.authenticated;
        } else {
          // Fetch fresh profile
          await fetchProfile();
        }
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (e) {
      debugPrint('Auth initialization error: $e');
      _status = AuthStatus.unauthenticated;
    } finally {
      _setLoading(false);
    }
  }

  /// Continue as guest without login
  Future<void> continueAsGuest() async {
    _setLoading(true);

    try {
      await _cache.setGuestMode(true);
      _status = AuthStatus.guest;
      _user = null;

      _setLoading(false);
      notifyListeners();
    } catch (e) {
      debugPrint('Guest mode error: $e');
      _setLoading(false);
    }
  }

  /// Request OTP for login (account must already exist)
  Future<bool> requestLoginOtp(String phoneNumber) async {
    _setLoading(true);
    _clearError();

    try {
      await _api.post(ApiConfig.authLogin, {
        'phone_number': phoneNumber,
        'intent': 'login',
      });

      _setLoading(false);
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  /// Request OTP for registration (new account)
  Future<bool> requestRegisterOtp(String phoneNumber) async {
    _setLoading(true);
    _clearError();

    try {
      await _api.post(ApiConfig.authLogin, {
        'phone_number': phoneNumber,
        'intent': 'register',
      });

      _setLoading(false);
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  /// Legacy: Request OTP (no intent)
  Future<bool> requestOtp(String phoneNumber) async {
    return requestLoginOtp(phoneNumber);
  }

  /// Verify OTP for login
  Future<bool> verifyLoginOtp(String phoneNumber, String otp) async {
    _setLoading(true);
    _clearError();

    try {
      final response = await _api.post(ApiConfig.authVerify, {
        'phone_number': phoneNumber,
        'otp_code': otp,
        'intent': 'login',
      });

      final token = response['access_token'];
      if (token != null) {
        await _tokenStore.saveToken(token);
        await _tokenStore.savePhone(phoneNumber);
        if (response['refresh_token'] != null) {
          await _tokenStore.saveRefreshToken(response['refresh_token']);
        }
        await fetchProfile();
        _status = AuthStatus.authenticated;
        _setLoading(false);
        notifyListeners();
        return true;
      }

      // Cookie-based auth — build user from response
      _user = UserModel.fromJson(response);
      await _cache.cacheUserProfile(response);
      _status = AuthStatus.authenticated;
      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  /// Verify OTP for new account registration
  Future<bool> verifyRegisterOtp({
    required String phoneNumber,
    required String otp,
    required Map<String, dynamic> registrationData,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final response = await _api.post(ApiConfig.authVerify, {
        'phone_number': phoneNumber,
        'otp_code': otp,
        'intent': 'register',
        'registration': registrationData,
      });

      final token = response['access_token'];
      if (token != null) {
        await _tokenStore.saveToken(token);
        await _tokenStore.savePhone(phoneNumber);
        if (response['refresh_token'] != null) {
          await _tokenStore.saveRefreshToken(response['refresh_token']);
        }
      }

      // Build user from response
      _user = UserModel.fromJson(response);
      await _cache.cacheUserProfile(response);
      _status = AuthStatus.authenticated;
      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  /// Legacy verifyOtp (used by old OTP verification screen)
  Future<bool> verifyOtp(String phoneNumber, String otp) async {
    return verifyLoginOtp(phoneNumber, otp);
  }

  /// Fetch user profile
  Future<void> fetchProfile() async {
    try {
      final response = await _api.get(ApiConfig.authProfile);
      _user = UserModel.fromJson(response);

      // Cache profile
      await _cache.cacheUserProfile(response);

      _status = AuthStatus.authenticated;
      notifyListeners();
    } catch (e) {
      debugPrint('Failed to fetch profile: $e');
      _setError('Failed to load profile');
    }
  }

  /// Update user profile
  Future<bool> updateProfile(Map<String, dynamic> updates) async {
    _setLoading(true);
    _clearError();

    try {
      final response = await _api.put(ApiConfig.authProfile, updates);
      _user = UserModel.fromJson(response);

      // Update cache
      await _cache.cacheUserProfile(response);

      _setLoading(false);
      notifyListeners();
      return true;
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      return false;
    }
  }

  /// Logout user and clear guest mode
  Future<void> logout() async {
    _setLoading(true);

    try {
      // Clear tokens
      await _tokenStore.clearAll();

      // Clear cache including guest mode
      await _cache.clearAll();

      _user = null;
      _status = AuthStatus.unauthenticated;

      _setLoading(false);
      notifyListeners();
    } catch (e) {
      debugPrint('Logout error: $e');
      _setLoading(false);
    }
  }

  /// Refresh auth token
  Future<bool> refreshToken() async {
    try {
      final refreshToken = await _tokenStore.readRefreshToken();

      if (refreshToken == null) {
        return false;
      }

      final response = await _api.post(ApiConfig.authRefresh, {
        'refresh_token': refreshToken,
      });

      final newToken = response['access_token'];
      if (newToken != null) {
        await _tokenStore.saveToken(newToken);
        return true;
      }

      return false;
    } catch (e) {
      debugPrint('Token refresh failed: $e');
      return false;
    }
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _setError(String message) {
    _errorMessage = message;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
  }
}
