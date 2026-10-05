import 'package:go_router/go_router.dart';
import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';
import '../features/home/screens/landing_screen.dart';
import '../features/auth/screens/splash_screen.dart';
import '../features/auth/screens/language_selection_screen.dart';
import '../features/auth/screens/premium_login_screen.dart';
import '../features/auth/screens/otp_verification_screen.dart';
import '../features/home/screens/home_shell.dart';
import '../features/voice/screens/premium_voice_screen_v2.dart';
import '../features/schemes/screens/schemes_screen.dart';
import '../features/schemes/screens/scheme_detail_screen.dart';
import '../features/grievances/screens/grievances_screen.dart';
import '../features/grievances/screens/create_grievance_screen.dart';
import '../features/grievances/screens/grievance_detail_screen.dart';
import '../features/knowledge/screens/knowledge_base_screen.dart';
import '../features/profile/screens/premium_profile_screen.dart';
import '../features/profile/screens/edit_profile_screen.dart';
import '../features/profile/screens/settings_screen.dart';

/// Premium application router - Simplified to match website features
class AppRouter {
  static final GoRouter router = GoRouter(
    initialLocation: '/splash',
    routes: [
      // Splash and Onboarding
      GoRoute(
        path: '/splash',
        name: 'splash',
        builder: (context, state) => const SplashScreen(),
      ),
      
      GoRoute(
        path: '/landing',
        name: 'landing',
        builder: (context, state) => const LandingScreen(),
      ),
      
      GoRoute(
        path: '/language-selection',
        name: 'language-selection',
        builder: (context, state) => const LanguageSelectionScreen(),
      ),
      
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const PremiumLoginScreen(),
      ),

      GoRoute(
        path: '/register',
        name: 'register',
        builder: (context, state) => const PremiumLoginScreen(isRegistering: true),
      ),
      
      GoRoute(
        path: '/otp-verification',
        name: 'otp-verification',
        builder: (context, state) {
          final extra = state.extra;
          String phone = '';
          bool isRegistering = false;
          
          if (extra is String) {
            phone = extra;
          } else if (extra is Map<String, dynamic>) {
            phone = extra['phone'] as String? ?? '';
            isRegistering = extra['isRegistering'] as bool? ?? false;
          }
          
          return OtpVerificationScreen(
            phoneNumber: phone,
            isRegistering: isRegistering,
          );
        },
      ),

      // Main App Shell with Bottom Navigation
      // Features: Voice, Schemes, Grievances, Profile (matching website)
      ShellRoute(
        builder: (context, state, child) {
          return HomeShell(child: child);
        },
        routes: [
          GoRoute(
            path: '/home',
            name: 'home',
            redirect: (context, state) => '/ask-sahayak',
          ),
          
          // Voice Assistant (Primary feature)
          GoRoute(
            path: '/ask-sahayak',
            name: 'ask-sahayak',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const PremiumVoiceScreenV2(),
            ),
          ),
          
          // Government Schemes
          GoRoute(
            path: '/schemes',
            name: 'schemes',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const SchemesScreen(),
            ),
          ),
          
          // Grievances
          GoRoute(
            path: '/grievances',
            name: 'grievances',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const GrievancesScreen(),
            ),
          ),
          
          // Knowledge Base
          GoRoute(
            path: '/knowledge',
            name: 'knowledge',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const KnowledgeBaseScreen(),
            ),
          ),
          
          // Profile
          GoRoute(
            path: '/profile',
            name: 'profile',
            pageBuilder: (context, state) => NoTransitionPage(
              child: const PremiumProfileScreen(),
            ),
          ),
        ],
      ),

      // Scheme Details
      GoRoute(
        path: '/scheme/:id',
        name: 'scheme-detail',
        builder: (context, state) {
          final id = state.pathParameters['id']!;
          return SchemeDetailScreen(schemeId: id);
        },
      ),

      // Create Grievance
      GoRoute(
        path: '/grievances/create',
        name: 'create-grievance',
        builder: (context, state) => const CreateGrievanceScreen(),
      ),
      
      // Grievance Detail
      GoRoute(
        path: '/grievances/:id',
        name: 'grievance-detail',
        builder: (context, state) {
          final id = state.pathParameters['id']!;
          return GrievanceDetailScreen(grievanceId: id);
        },
      ),

      // Profile & Settings
      GoRoute(
        path: '/profile/edit',
        name: 'edit-profile',
        builder: (context, state) => const EditProfileScreen(),
      ),
      
      GoRoute(
        path: '/settings',
        name: 'settings',
        builder: (context, state) => const SettingsScreen(),
      ),
    ],
    
    // Error handling
    errorBuilder: (context, state) => Scaffold(
      backgroundColor: AppColors.canvas,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline_rounded,
              size: 64,
              color: AppColors.error,
            ),
            const SizedBox(height: 24),
            Text(
              'Page not found',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w600,
                color: AppColors.ink,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              state.uri.path,
              style: TextStyle(
                fontSize: 14,
                color: AppColors.muted,
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => context.go('/ask-sahayak'),
              icon: const Icon(Icons.home_rounded),
              label: const Text('Go Home'),
            ),
          ],
        ),
      ),
    ),
  );
}

