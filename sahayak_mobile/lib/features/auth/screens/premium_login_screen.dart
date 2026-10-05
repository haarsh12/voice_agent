import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/widgets/premium_button.dart';
import '../providers/auth_provider.dart';

/// Premium login screen with smooth animations
class PremiumLoginScreen extends StatefulWidget {
  final bool isRegistering;
  const PremiumLoginScreen({super.key, this.isRegistering = false});

  @override
  State<PremiumLoginScreen> createState() => _PremiumLoginScreenState();
}

class _PremiumLoginScreenState extends State<PremiumLoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    HapticFeedback.mediumImpact();

    try {
      final authProvider = context.read<AuthProvider>();
      final phone = _phoneController.text.trim();
      
      // Send OTP
      final success = widget.isRegistering 
          ? await authProvider.requestRegisterOtp(phone)
          : await authProvider.requestLoginOtp(phone);
      
      if (!success) {
        throw Exception('Failed to send OTP');
      }
      
      if (mounted) {
        context.push('/otp-verification', extra: {
          'phone': phone,
          'isRegistering': widget.isRegistering,
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.ink),
          onPressed: () {
            if (context.canPop()) {
              context.pop();
            } else {
              context.go('/landing');
            }
          },
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),

                // Header
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.isRegistering ? 'Create Account' : 'Welcome back',
                      style: const TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                        letterSpacing: -1.8,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      widget.isRegistering 
                          ? 'Register to track your grievances and save profile info'
                          : 'Sign in to access your profile and saved information',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w400,
                        color: AppColors.muted,
                        height: 1.5,
                      ),
                    ),
                  ],
                )
                    .animate()
                    .fadeIn(duration: 400.ms)
                    .slideY(begin: -0.1, end: 0),

                const SizedBox(height: 48),

                // Phone input
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Phone Number',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.ink,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      maxLength: 10,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        color: AppColors.ink,
                      ),
                      decoration: InputDecoration(
                        hintText: '9876543210',
                        prefixIcon: Container(
                          padding: const EdgeInsets.only(left: 16, right: 8),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text(
                                '+91',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.ink,
                                ),
                              ),
                              Container(
                                width: 1,
                                height: 20,
                                margin: const EdgeInsets.only(left: 12),
                                color: AppColors.line,
                              ),
                            ],
                          ),
                        ),
                        counterText: '',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your phone number';
                        }
                        if (value.length != 10) {
                          return 'Phone number must be 10 digits';
                        }
                        if (!RegExp(r'^[0-9]+$').hasMatch(value)) {
                          return 'Please enter only numbers';
                        }
                        return null;
                      },
                    ),
                  ],
                ).animate().fadeIn(delay: 200.ms, duration: 400.ms),

                const SizedBox(height: 32),

                // Login button
                PremiumButton(
                  text: 'Continue with OTP',
                  onPressed: _isLoading ? null : _handleLogin,
                  isLoading: _isLoading,
                  icon: Icons.arrow_forward_rounded,
                ).animate().fadeIn(delay: 300.ms, duration: 400.ms),

                const SizedBox(height: 24),

                // Guest mode link
                Center(
                  child: TextButton(
                    onPressed: () => context.go('/schemes'),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.person_outline_rounded,
                          size: 18,
                          color: AppColors.muted,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'Continue as Guest',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.muted,
                            decoration: TextDecoration.underline,
                            decorationColor: AppColors.muted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ).animate().fadeIn(delay: 400.ms),

              ],
            ),
          ),
        ),
      ),
    );
  }
}
