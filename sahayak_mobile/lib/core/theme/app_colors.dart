import 'package:flutter/material.dart';

/// Premium color palette for Sahayak AI - Modern bright design
/// Clean, professional with vibrant accents
class AppColors {
  const AppColors._();

  // Primary Colors - Modern bright palette
  static const Color primary = Color(0xFF1A1A1A); // Rich black for premium feel
  static const Color primaryHover = Color(0xFF2D2D2D);
  static const Color primaryLight = Color(0xFF3D3D3D);
  static const Color primaryDark = Color(0xFF000000);
  
  // Accent Colors - Vibrant and modern
  static const Color accent = Color(0xFF6366F1); // Indigo
  static const Color accentLight = Color(0xFF818CF8);
  static const Color accentDark = Color(0xFF4F46E5);
  
  // Green Accent - Success & Active states
  static const Color green = Color(0xFF10B981); // Bright emerald
  static const Color greenPale = Color(0xFFD1FAE5);
  static const Color greenDark = Color(0xFF059669);
  
  // Orange Accent - Warm highlights
  static const Color orange = Color(0xFFFF6B6B);
  static const Color orangeLight = Color(0xFFFFE5E5);
  
  // Purple Accent - Premium feel
  static const Color purple = Color(0xFF8B5CF6);
  static const Color purpleLight = Color(0xFFF3E8FF);
  
  // Blue Accent - Info & Links
  static const Color blue = Color(0xFF3B82F6);
  static const Color blueLight = Color(0xFFDBEAFE);
  
  // Ink & Text - High contrast
  static const Color ink = Color(0xFF000000);
  static const Color muted = Color(0xFF4B5563);
  static const Color textPrimary = Color(0xFF111827);
  static const Color textSecondary = Color(0xFF4B5563);
  static const Color textTertiary = Color(0xFF9CA3AF);
  
  // Background & Surface - Clean and bright
  static const Color canvas = Color(0xFFFFFFFF); // Pure white background
  static const Color background = Color(0xFFFFFFFF);
  static const Color surface = Color(0xFFFFFFFF); // Pure white
  static const Color surfaceAlt = Color(0xFFF9FAFB);
  static const Color subtle = Color(0xFFF3F4F6);
  
  // Borders & Lines - Subtle
  static const Color line = Color(0xFFE5E7EB);
  static const Color border = Color(0xFFE5E7EB);
  static const Color strongLine = Color(0xFFD1D5DB);
  static const Color divider = Color(0xFFF3F4F6);
  
  // Surface variants
  static const Color surfaceVariant = Color(0xFFF3F4F6);
  static const Color secondary = Color(0xFF6B7280);
  
  // Status Colors
  static const Color success = Color(0xFF10B981);
  static const Color successLight = Color(0xFFD1FAE5);
  
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningLight = Color(0xFFFEF3C7);
  
  static const Color error = Color(0xFFEF4444);
  static const Color errorLight = Color(0xFFFEE2E2);
  static const Color danger = Color(0xFFEF4444);
  
  static const Color info = Color(0xFF3B82F6);
  static const Color infoLight = Color(0xFFDBEAFE);
  
  // Interactive Elements
  static const Color chipBackground = Color(0xFFF3F4F6);
  static const Color inputBackground = Color(0xFFFFFFFF);
  static const Color hoverBackground = Color(0xFFF9FAFB);
  static const Color pressedBackground = Color(0xFFF3F4F6);
  static const Color ripple = Color(0x1A6366F1);
  
  // Shadows - Modern soft shadows
  static const Color shadow = Color(0x0F000000);
  static const Color shadowRaised = Color(0x1A000000);
  
  // Voice Assistant Colors
  static const Color voiceActive = Color(0xFF10B981);
  static const Color voiceInactive = Color(0xFF9CA3AF);
  static const Color voiceListening = Color(0xFF10B981);
  static const Color voiceThinking = Color(0xFF8B5CF6);
  static const Color voiceError = Color(0xFFEF4444);
  static const Color voiceOrb = Color(0xFFFFFFFF);
  static const Color voiceOrbBorder = Color(0xFFE5E7EB);
  
  // Language Selector
  static const Color languageSelected = Color(0xFFEEF2FF);
  static const Color languageSelectedBorder = Color(0xFF6366F1);
  static const Color languageUnselected = Color(0xFFFFFFFF);
  
  // Connection Status
  static const Color connected = Color(0xFF10B981);
  static const Color connecting = Color(0xFFF59E0B);
  static const Color disconnected = Color(0xFF9CA3AF);
  
  // Category Colors - Vibrant modern palette
  static const Color agriculture = Color(0xFF10B981);
  static const Color health = Color(0xFFEF4444);
  static const Color education = Color(0xFF3B82F6);
  static const Color finance = Color(0xFFF59E0B);
  static const Color social = Color(0xFF8B5CF6);
  static const Color infrastructure = Color(0xFF6B7280);
  
  // Premium Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF1A1A1A), Color(0xFF2D2D2D)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient accentGradient = LinearGradient(
    colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient greenGradient = LinearGradient(
    colors: [Color(0xFF10B981), Color(0xFF059669)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient surfaceGradient = LinearGradient(
    colors: [Color(0xFFFFFFFF), Color(0xFFF9FAFB)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );
  
  static const LinearGradient canvasGradient = LinearGradient(
    colors: [Color(0xFFF9FAFB), Color(0xFFF3F4F6)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );
  
  static const LinearGradient orangeGradient = LinearGradient(
    colors: [Color(0xFFFF6B6B), Color(0xFFFF8E53)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Box Shadows - Modern neumorphism
  static List<BoxShadow> get cardShadow => [
    const BoxShadow(
      color: Color(0x0A000000),
      offset: Offset(0, 4),
      blurRadius: 16,
      spreadRadius: 0,
    ),
    const BoxShadow(
      color: Color(0x05000000),
      offset: Offset(0, 2),
      blurRadius: 8,
      spreadRadius: 0,
    ),
  ];

  static List<BoxShadow> get raisedShadow => [
    const BoxShadow(
      color: Color(0x14000000),
      offset: Offset(0, 10),
      blurRadius: 24,
      spreadRadius: 0,
    ),
    const BoxShadow(
      color: Color(0x0A000000),
      offset: Offset(0, 4),
      blurRadius: 12,
      spreadRadius: 0,
    ),
  ];
  
  static List<BoxShadow> get buttonShadow => [
    BoxShadow(
      color: const Color(0xFF6366F1).withOpacity(0.25),
      offset: const Offset(0, 4),
      blurRadius: 12,
      spreadRadius: 0,
    ),
  ];
  
  static List<BoxShadow> get glowShadow => [
    BoxShadow(
      color: const Color(0xFF10B981).withOpacity(0.3),
      offset: const Offset(0, 0),
      blurRadius: 20,
      spreadRadius: 0,
    ),
  ];
}
