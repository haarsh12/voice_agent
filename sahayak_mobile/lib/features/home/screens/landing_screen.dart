import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/widgets/premium_button.dart';

/// Premium landing screen with Airbnb-style design
class LandingScreen extends StatelessWidget {
  const LandingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Logo
              Row(
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(11),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: const Icon(
                      Icons.support_agent_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 9),
                  const Text(
                    'Sahayak',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: AppColors.ink,
                      letterSpacing: -0.5,
                    ),
                  ),
                ],
              ).animate().fadeIn(duration: 400.ms).slideY(
                    begin: -0.2,
                    end: 0,
                    curve: Curves.easeOut,
                  ),

              const SizedBox(height: 72),

              // Hero Section
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Kicker
                  Text(
                    'WELCOME TO'.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: AppColors.primary,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Main headline
                  const Text(
                    'Your AI Assistant\nfor Government\nServices',
                    style: TextStyle(
                      fontSize: 42,
                      fontWeight: FontWeight.w700,
                      color: AppColors.ink,
                      height: 1.05,
                      letterSpacing: -2.5,
                    ),
                  ),
                  const SizedBox(height: 23),

                  // Description
                  Text(
                    'Get instant help with schemes, grievances, and government services. Available in 10 Indian languages with voice support.',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                      color: AppColors.muted,
                      height: 1.65,
                      letterSpacing: -0.2,
                    ),
                  ),
                ],
              )
                  .animate()
                  .fadeIn(delay: 200.ms, duration: 600.ms)
                  .slideY(begin: 0.2, end: 0, curve: Curves.easeOut),

              const SizedBox(height: 48),

              // Action buttons
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  PremiumButton(
                    text: 'Start with Voice',
                    icon: Icons.mic_rounded,
                    onPressed: () => context.go('/ask-sahayak'),
                  ),
                  const SizedBox(height: 12),
                  PremiumButton(
                    text: 'Browse as Guest',
                    style: PremiumButtonStyle.outline,
                    icon: Icons.explore_outlined,
                    onPressed: () => context.go('/schemes'),
                  ),
                  const SizedBox(height: 24),
                  Center(
                    child: TextButton(
                      onPressed: () => context.go('/login'),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text(
                            'Already have an account?',
                            style: TextStyle(
                              fontSize: 14,
                              color: AppColors.muted,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'Sign in',
                            style: const TextStyle(
                              fontSize: 14,
                              color: AppColors.ink,
                              fontWeight: FontWeight.w700,
                              decoration: TextDecoration.underline,
                              decorationColor: AppColors.ink,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              )
                  .animate()
                  .fadeIn(delay: 400.ms, duration: 600.ms)
                  .slideY(begin: 0.1, end: 0, curve: Curves.easeOut),

              const SizedBox(height: 60),

              // Trust indicators
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _TrustBadge(
                    icon: Icons.verified_user_rounded,
                    label: 'Secure',
                  ),
                  Container(
                    width: 4,
                    height: 4,
                    margin: const EdgeInsets.symmetric(horizontal: 15),
                    decoration: const BoxDecoration(
                      color: Color(0xFFB7B7B7),
                      shape: BoxShape.circle,
                    ),
                  ),
                  _TrustBadge(
                    icon: Icons.language_rounded,
                    label: '10 Languages',
                  ),
                  Container(
                    width: 4,
                    height: 4,
                    margin: const EdgeInsets.symmetric(horizontal: 15),
                    decoration: const BoxDecoration(
                      color: Color(0xFFB7B7B7),
                      shape: BoxShape.circle,
                    ),
                  ),
                  _TrustBadge(
                    icon: Icons.support_rounded,
                    label: '24/7 Available',
                  ),
                ],
              )
                  .animate()
                  .fadeIn(delay: 600.ms, duration: 600.ms)
                  .slideY(begin: 0.1, end: 0),

              const SizedBox(height: 40),

              // Features preview
              _FeatureCard(
                icon: Icons.campaign_rounded,
                title: 'Voice First',
                description:
                    'Talk naturally in your language. Our AI understands and responds.',
              ).animate().fadeIn(delay: 700.ms).slideX(begin: -0.1, end: 0),

              const SizedBox(height: 16),

              _FeatureCard(
                icon: Icons.account_balance_rounded,
                title: 'Government Schemes',
                description:
                    'Discover schemes you qualify for and learn how to apply.',
              ).animate().fadeIn(delay: 800.ms).slideX(begin: -0.1, end: 0),

              const SizedBox(height: 16),

              _FeatureCard(
                icon: Icons.support_agent_rounded,
                title: 'Report Issues',
                description:
                    'Submit grievances and track their resolution status easily.',
              ).animate().fadeIn(delay: 900.ms).slideX(begin: -0.1, end: 0),
            ],
          ),
        ),
      ),
    );
  }
}

class _TrustBadge extends StatelessWidget {
  final IconData icon;
  final String label;

  const _TrustBadge({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: AppColors.ink),
        const SizedBox(width: 5),
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: Color(0xFF5B5B5B),
          ),
        ),
      ],
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;

  const _FeatureCard({
    required this.icon,
    required this.title,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE5E5E5), width: 1),
        boxShadow: [
          BoxShadow(
            color: AppColors.shadow,
            offset: const Offset(0, 2),
            blurRadius: 9,
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.surfaceAlt,
              borderRadius: BorderRadius.circular(11),
            ),
            child: Icon(icon, color: AppColors.ink, size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppColors.ink,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w400,
                    color: AppColors.muted,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
