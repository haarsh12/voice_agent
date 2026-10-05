import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart' as local_auth;
import '../../../core/theme/app_colors.dart';
import '../../../shared/widgets/premium_card.dart';
import '../../auth/providers/auth_provider.dart';
import '../../../shared/providers/language_provider.dart';

/// Premium profile screen with guest mode support
class PremiumProfileScreen extends StatelessWidget {
  const PremiumProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final languageProvider = context.watch<LanguageProvider>();
    final isGuest = !authProvider.isAuthenticated;
    final user = authProvider.user;

    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        title: const Text('Profile'),
        actions: [
          if (!isGuest)
            IconButton(
              icon: const Icon(Icons.settings_outlined, color: AppColors.ink),
              onPressed: () => context.push('/settings'),
            ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Profile header
              _buildProfileHeader(context, isGuest, user)
                  .animate()
                  .fadeIn(duration: 400.ms)
                  .slideY(begin: -0.1, end: 0),

              const SizedBox(height: 32),

              // Preferences (available for all)
              _buildSection('Preferences'),
              const SizedBox(height: 12),
              _buildInfoTile(
                icon: Icons.language_rounded,
                label: 'Language',
                value: languageProvider.currentLanguageName,
                trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16),
                iconColor: AppColors.ink,
                onTap: () => _showLanguageSelector(context),
              ).animate().fadeIn(delay: 450.ms),

              const SizedBox(height: 24),

              // Actions
              _buildSection('Account'),
              const SizedBox(height: 12),

              if (isGuest) ...[
                // Sign In
                _buildActionCard(
                  title: 'Sign In',
                  subtitle: 'Access your saved profile',
                  icon: Icons.login_rounded,
                  color: AppColors.ink,
                  onTap: () {
                    HapticFeedback.lightImpact();
                    context.go('/login');
                  },
                ).animate().fadeIn(delay: 500.ms),

                // Create Account
                _buildActionCard(
                  title: 'Create Account',
                  subtitle: 'Register a new Sahayak account',
                  icon: Icons.person_add_rounded,
                  color: AppColors.primary,
                  onTap: () {
                    HapticFeedback.lightImpact();
                    context.go('/register'); // Assume there's a route or we can create one
                  },
                ).animate().fadeIn(delay: 550.ms),

                // Login with Face ID
                _buildActionCard(
                  title: 'Login with Face ID',
                  subtitle: 'Quick and secure access',
                  icon: Icons.face_rounded,
                  color: AppColors.ink,
                  onTap: () async {
                    HapticFeedback.lightImpact();
                    try {
                      final auth = local_auth.LocalAuthentication();
                      final canAuth = await auth.canCheckBiometrics || await auth.isDeviceSupported();
                      if (canAuth) {
                        final didAuth = await auth.authenticate(
                          localizedReason: 'Please authenticate to login',
                          options: const local_auth.AuthenticationOptions(biometricOnly: true),
                        );
                        if (didAuth) {
                          // Note: In a real app, we would use WebAuthn passkeys or retrieve a securely stored token here.
                          // For now, we simulate a successful biometric verification but require them to login first if no token exists.
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Face ID recognized. Please sign in with OTP once to link this device.')),
                          );
                        }
                      }
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Face ID failed: $e')),
                      );
                    }
                  },
                ).animate().fadeIn(delay: 600.ms),

                const SizedBox(height: 24),
                
                // Guest mode banner moved down
                _buildGuestBanner(context)
                    .animate()
                    .fadeIn(delay: 650.ms, duration: 400.ms)
                    .slideY(begin: 0.1, end: 0),
                const SizedBox(height: 8),
              ] else ...[
                // Logout button for authenticated users
                PremiumCard(
                  onTap: () => _handleLogout(context, authProvider),
                  padding: const EdgeInsets.all(18),
                  backgroundColor: AppColors.errorLight,
                  showBorder: true,
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.error.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.logout_rounded,
                          color: AppColors.error,
                          size: 22,
                        ),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Text(
                          'Logout',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: AppColors.error,
                          ),
                        ),
                      ),
                      const Icon(
                        Icons.arrow_forward_rounded,
                        color: AppColors.error,
                        size: 20,
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 500.ms),
              ],

              const SizedBox(height: 32),

              // App info
              Center(
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.support_agent_rounded,
                        color: AppColors.primary,
                        size: 32,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Sahayak AI',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Version 1.0.0',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppColors.muted,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '© Sahayak AI\nYour Government Assistant',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.muted,
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn(delay: 600.ms),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileHeader(BuildContext context, bool isGuest, dynamic user) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E5E5), width: 1),
        boxShadow: AppColors.cardShadow,
      ),
      child: Column(
        children: [
          // Avatar
          Stack(
            children: [
              Container(
                width: 90,
                height: 90,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: isGuest
                      ? LinearGradient(
                          colors: [
                            AppColors.muted.withOpacity(0.2),
                            AppColors.muted.withOpacity(0.1),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        )
                      : AppColors.greenGradient,
                  boxShadow: [
                    BoxShadow(
                      color: isGuest
                          ? AppColors.shadow
                          : AppColors.green.withOpacity(0.2),
                      blurRadius: 16,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Icon(
                  isGuest ? Icons.person_outline_rounded : Icons.person_rounded,
                  size: 42,
                  color: isGuest ? AppColors.muted : Colors.white,
                ),
              ),
              if (isGuest)
                Positioned(
                  right: 0,
                  bottom: 0,
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: AppColors.warning,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.surface, width: 3),
                    ),
                    child: const Icon(
                      Icons.lock_outline_rounded,
                      size: 14,
                      color: Colors.white,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 16),

          // Name
          Text(
            isGuest ? 'Guest User' : (user?.name ?? 'User'),
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w700,
              color: AppColors.ink,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),

          // Status
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: isGuest
                  ? AppColors.warningLight
                  : AppColors.successLight,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isGuest
                    ? AppColors.warning.withOpacity(0.3)
                    : AppColors.success.withOpacity(0.3),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: isGuest ? AppColors.warning : AppColors.success,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  isGuest ? 'Guest Mode' : 'Verified Account',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isGuest ? AppColors.warning : AppColors.success,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuestBanner(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.greenPale,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppColors.green.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.green.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.info_outline_rounded,
              color: AppColors.green,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Why Create an Account?',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppColors.green,
                  ),
                ),
                SizedBox(height: 6),
                Text(
                  '• Track your grievances and requests\n'
                  '• Get personalized scheme recommendations\n'
                  '• Save and sync your profile across devices\n'
                  '• Access full conversation history',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.green,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: AppColors.muted,
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildInfoTile({
    required IconData icon,
    required String label,
    required String value,
    Widget? trailing,
    Color iconColor = AppColors.green,
    VoidCallback? onTap,
  }) {
    return PremiumCard(
      onTap: onTap,
      padding: const EdgeInsets.all(16),
      margin: EdgeInsets.zero,
      enableAnimation: onTap != null,
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: AppColors.muted,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.ink,
                  ),
                ),
              ],
            ),
          ),
          if (trailing != null)
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: trailing,
            ),
        ],
      ),
    );
  }

  Widget _buildActionCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return PremiumCard(
      onTap: onTap,
      padding: const EdgeInsets.all(18),
      margin: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              icon,
              color: color,
              size: 22,
            ),
          ),
          const SizedBox(width: 14),
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
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.muted,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          const Icon(
            Icons.arrow_forward_rounded,
            color: AppColors.muted,
            size: 20,
          ),
        ],
      ),
    );
  }

  void _showLanguageSelector(BuildContext context) {
    final languageProvider = context.read<LanguageProvider>();

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.greenPale,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.language_rounded,
                        color: AppColors.green,
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Text(
                      'Select Language',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                ...LanguageProvider.supportedLocales.map((locale) {
                  final code = locale.languageCode;
                  final isSelected =
                      languageProvider.currentLanguageCode == code;

                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? AppColors.greenPale
                          : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isSelected
                            ? AppColors.green
                            : const Color(0xFFE5E5E5),
                        width: isSelected ? 2 : 1,
                      ),
                    ),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 4,
                      ),
                      leading: Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppColors.green
                              : AppColors.subtle,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          isSelected
                              ? Icons.check_rounded
                              : Icons.language_rounded,
                          color: isSelected
                              ? Colors.white
                              : AppColors.muted,
                          size: 20,
                        ),
                      ),
                      title: Text(
                        LanguageProvider.languageNames[code] ?? '',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight:
                              isSelected ? FontWeight.w600 : FontWeight.w500,
                          color: isSelected ? AppColors.green : AppColors.ink,
                        ),
                      ),
                      subtitle: Text(
                        LanguageProvider.languageScriptNames[code] ?? '',
                        style: TextStyle(
                          fontSize: 13,
                          color: isSelected
                              ? AppColors.green.withOpacity(0.7)
                              : AppColors.muted,
                        ),
                      ),
                      onTap: () {
                        HapticFeedback.lightImpact();
                        languageProvider.setLanguage(code);
                        Navigator.pop(context);
                      },
                    ),
                  );
                }).toList(),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _handleLogout(
      BuildContext context, AuthProvider authProvider) async {
    HapticFeedback.mediumImpact();

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text(
          'Confirm Logout',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: AppColors.ink,
          ),
        ),
        content: const Text(
          'Are you sure you want to logout? You can always sign in again later.',
          style: TextStyle(
            fontSize: 15,
            color: AppColors.muted,
            height: 1.5,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
            ),
            child: const Text('Logout'),
          ),
        ],
      ),
    );

    if (confirm == true && context.mounted) {
      await authProvider.logout();
      if (context.mounted) {
        HapticFeedback.lightImpact();
        context.go('/landing');
      }
    }
  }
}
