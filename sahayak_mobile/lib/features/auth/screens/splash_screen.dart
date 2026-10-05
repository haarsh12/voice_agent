import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/providers/language_provider.dart';
import '../providers/auth_provider.dart';

/// Splash screen with app logo and initialization
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    final authProvider = context.read<AuthProvider>();
    final languageProvider = context.read<LanguageProvider>();

    // Wait for minimum splash duration
    await Future.delayed(const Duration(seconds: 2));

    // Initialize auth state
    await authProvider.initialize();

    if (!mounted) return;

    // Check language selection
    final isLanguageSelected = await languageProvider.isLanguageSelected();

    if (!isLanguageSelected) {
      // First time - show language selection
      context.go('/language-selection');
    } else if (authProvider.isAuthenticated) {
      // Already logged in - go to home (voice page)
      context.go('/ask-sahayak');
    } else {
      // Not logged in - go directly to app in guest mode
      await authProvider.continueAsGuest();
      context.go('/ask-sahayak');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo placeholder
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.3),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: const Icon(
                Icons.support_agent,
                size: 60,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 24),
            
            // App name
            const Text(
              'Sahayak AI',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 8),
            
            // Tagline
            Text(
              'Your Government Assistant',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w400,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 48),
            
            // Loading indicator
            const SizedBox(
              width: 40,
              height: 40,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: AppColors.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
