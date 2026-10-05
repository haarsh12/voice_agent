import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Manages app language selection and persistence
class LanguageProvider extends ChangeNotifier {
  static const String _languageKey = 'selected_language';
  
  Locale _currentLocale = const Locale('hi', 'IN'); // Default to Hindi (India)

  Locale get currentLocale => _currentLocale;
  
  String get currentLanguageCode => _currentLocale.languageCode;
  
  String get currentLanguageName => _getLanguageName(_currentLocale.languageCode);

  // Supported languages in Sahayak
  static const List<Locale> supportedLocales = [
    Locale('hi', 'IN'), // Hindi
    Locale('mr', 'IN'), // Marathi
    Locale('en', 'IN'), // English
    Locale('ta', 'IN'), // Tamil
    Locale('te', 'IN'), // Telugu
    Locale('kn', 'IN'), // Kannada
    Locale('ml', 'IN'), // Malayalam
    Locale('gu', 'IN'), // Gujarati
    Locale('bn', 'IN'), // Bengali
    Locale('pa', 'IN'), // Punjabi
  ];

  // Language display names
  static const Map<String, String> languageNames = {
    'hi': 'हिंदी',
    'mr': 'मराठी',
    'en': 'English',
    'ta': 'தமிழ்',
    'te': 'తెలుగు',
    'kn': 'ಕನ್ನಡ',
    'ml': 'മലയാളം',
    'gu': 'ગુજરાતી',
    'bn': 'বাংলা',
    'pa': 'ਪੰਜਾਬੀ',
  };

  // Language native script names
  static const Map<String, String> languageScriptNames = {
    'hi': 'Hindi',
    'mr': 'Marathi',
    'en': 'English',
    'ta': 'Tamil',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'gu': 'Gujarati',
    'bn': 'Bengali',
    'pa': 'Punjabi',
  };

  LanguageProvider() {
    _loadLanguage();
  }

  /// Load saved language from SharedPreferences
  Future<void> _loadLanguage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final languageCode = prefs.getString(_languageKey);
      
      if (languageCode != null) {
        final locale = supportedLocales.firstWhere(
          (l) => l.languageCode == languageCode,
          orElse: () => const Locale('hi', 'IN'),
        );
        _currentLocale = locale;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error loading language: $e');
    }
  }

  /// Set language and persist
  Future<void> setLanguage(String languageCode) async {
    try {
      final locale = supportedLocales.firstWhere(
        (l) => l.languageCode == languageCode,
        orElse: () => const Locale('en', 'IN'),
      );

      _currentLocale = locale;
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_languageKey, languageCode);
      
      notifyListeners();
    } catch (e) {
      debugPrint('Error setting language: $e');
    }
  }

  /// Check if language is selected (not default)
  Future<bool> isLanguageSelected() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey(_languageKey);
  }

  /// Get language display name
  String _getLanguageName(String code) {
    return languageNames[code] ?? 'English';
  }

  /// Get language script name (in English)
  String getLanguageScriptName(String code) {
    return languageScriptNames[code] ?? 'English';
  }
}
