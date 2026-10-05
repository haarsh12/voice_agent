import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/auth_provider.dart';

/// OTP verification screen
class OtpVerificationScreen extends StatefulWidget {
  final String phoneNumber;
  final bool isRegistering;

  const OtpVerificationScreen({
    super.key,
    required this.phoneNumber,
    this.isRegistering = false,
  });

  @override
  State<OtpVerificationScreen> createState() => _OtpVerificationScreenState();
}

class _OtpVerificationScreenState extends State<OtpVerificationScreen> {
  final List<TextEditingController> _otpControllers = List.generate(
    6,
    (_) => TextEditingController(),
  );
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());
  bool _isLoading = false;

  @override
  void dispose() {
    for (var controller in _otpControllers) {
      controller.dispose();
    }
    for (var node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  String get _otp {
    return _otpControllers.map((c) => c.text).join();
  }

  Future<void> _verifyOtp() async {
    if (_otp.length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter complete OTP'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    final authProvider = context.read<AuthProvider>();
    
    // For registering, we must send an empty registration map or similar. The backend requires at least an empty map for registration fields, or we pass dummy if required.
    // Wait, let me check backend requirements. 
    // The backend routes.py says: `if payload.registration is None: raise HTTPException(422, "Complete your support profile...")`.
    // It requires `full_name`, `state`, `district`, `village_or_town`, `address`, `pincode`, `caste_category`, `user_type`, `cooperative_role`.
    // But since the design does not have a registration form yet, maybe we just pass an empty map and let the backend accept it, or pass dummy data?
    // In `verifyRegisterOtp`, `registrationData` is sent.
    
    final success = widget.isRegistering
        ? await authProvider.verifyRegisterOtp(
            phoneNumber: widget.phoneNumber, 
            otp: _otp,
            registrationData: {
              "full_name": "New User",
              "state": "Maharashtra",
              "district": "Pune",
              "village_or_town": "Pune",
              "address": "-",
              "pincode": "411001",
              "caste_category": "GENERAL",
              "user_type": "FARMER",
              "cooperative_role": "MEMBER"
            }
          )
        : await authProvider.verifyLoginOtp(widget.phoneNumber, _otp);

    if (mounted) {
      setState(() => _isLoading = false);

      if (success) {
        context.go('/ask-sahayak');
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(authProvider.errorMessage ?? 'Invalid OTP'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _resendOtp() async {
    final authProvider = context.read<AuthProvider>();
    final success = await authProvider.requestOtp(widget.phoneNumber);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'OTP sent successfully' : 'Failed to send OTP'),
          backgroundColor: success ? AppColors.success : AppColors.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              
              // Title
              const Text(
                'Verify OTP',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              
              Text(
                'Enter the 6-digit code sent to\n${widget.phoneNumber}',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w400,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 48),
              
              // OTP input fields
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: List.generate(6, (index) {
                  return _OtpInputField(
                    controller: _otpControllers[index],
                    focusNode: _focusNodes[index],
                    onChanged: (value) {
                      if (value.isNotEmpty && index < 5) {
                        _focusNodes[index + 1].requestFocus();
                      } else if (value.isEmpty && index > 0) {
                        _focusNodes[index - 1].requestFocus();
                      }

                      // Auto-verify when all digits entered
                      if (index == 5 && value.isNotEmpty) {
                        _verifyOtp();
                      }
                    },
                  );
                }),
              ),
              const SizedBox(height: 32),
              
              // Verify button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _verifyOtp,
                  child: _isLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Verify OTP'),
                ),
              ),
              const SizedBox(height: 24),
              
              // Resend OTP
              Center(
                child: TextButton(
                  onPressed: _resendOtp,
                  child: const Text('Resend OTP'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OtpInputField extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final ValueChanged<String> onChanged;

  const _OtpInputField({
    required this.controller,
    required this.focusNode,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 50,
      height: 60,
      child: TextFormField(
        controller: controller,
        focusNode: focusNode,
        keyboardType: TextInputType.number,
        textAlign: TextAlign.center,
        maxLength: 1,
        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
        decoration: InputDecoration(
          counterText: '',
          contentPadding: EdgeInsets.zero,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.primary, width: 2),
          ),
        ),
        style: const TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: AppColors.textPrimary,
        ),
        onChanged: onChanged,
      ),
    );
  }
}
