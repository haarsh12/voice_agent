/// Central API configuration for Sahayak AI mobile application
/// 
/// Override at build time using:
/// flutter run --dart-define=API_BASE_URL=http://your-server:8000
class ApiConfig {
  const ApiConfig._();

  // Default production URL - update this when deploying
  static const String _defaultUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://192.168.10.207:8000', // Laptop IP on same WiFi network
  );

  /// Base URL for all HTTP API calls
  static String get baseUrl => _defaultUrl.replaceFirst(RegExp(r'/+$'), '');

  /// Stable device declaration sent with every backend request. It is a
  /// delivery hint for the AI, never an authentication or authorization claim.
  static const String clientDevice = 'mobile-app';

  /// WebSocket URL derived from base URL
  static String get wsUrl {
    final base = baseUrl;
    if (base.startsWith('https://')) {
      return base.replaceFirst('https://', 'wss://');
    }
    if (base.startsWith('http://')) {
      return base.replaceFirst('http://', 'ws://');
    }
    return 'ws://$base';
  }

  // API Endpoints
  static const String auth = '/api/auth';
  static const String authLogin = '$auth/otp/request';
  static const String authVerify = '$auth/otp/verify';
  static const String authRefresh = '$auth/refresh';
  static const String authProfile = '$auth/profile';
  
  static const String voice = '/voice';
  static const String voiceToken = '/api/token';
  
  static const String services = '/api/services';
  static const String schemes = '/api/schemes';
  static const String grievances = '/api/grievances';
  static const String knowledge = '/api/knowledge';
  
  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
}
