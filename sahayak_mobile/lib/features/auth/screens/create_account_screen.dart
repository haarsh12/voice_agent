import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/auth_provider.dart';

/// Complete account creation screen with all profile fields
class CreateAccountScreen extends StatefulWidget {
  final String phoneNumber;

  const CreateAccountScreen({
    super.key,
    required this.phoneNumber,
  });

  @override
  State<CreateAccountScreen> createState() => _CreateAccountScreenState();
}

class _CreateAccountScreenState extends State<CreateAccountScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _stateController = TextEditingController();
  final _districtController = TextEditingController();
  final _villageController = TextEditingController();
  final _addressController = TextEditingController();
  final _pincodeController = TextEditingController();
  
  String _casteCategory = 'GENERAL';
  String _userType = 'FARMER';
  String _cooperativeRole = 'MEMBER';
  
  bool _isLoading = false;

  @override
  void dispose() {
    _fullNameController.dispose();
    _stateController.dispose();
    _districtController.dispose();
    _villageController.dispose();
    _addressController.dispose();
    _pincodeController.dispose();
    super.dispose();
  }

  Future<void> _requestOtp() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    final authProvider = context.read<AuthProvider>();
    final success = await authProvider.requestOtp(widget.phoneNumber);

    if (mounted) {
      setState(() => _isLoading = false);

      if (success) {
        // Navigate to OTP screen with registration data
        context.push(
          '/otp-verification',
          extra: {
            'phoneNumber': widget.phoneNumber,
            'isRegistering': true,
            'registrationData': {
              'full_name': _fullNameController.text.trim(),
              'state': _stateController.text.trim(),
              'district': _districtController.text.trim(),
              'village_or_town': _villageController.text.trim(),
              'address': _addressController.text.trim(),
              'pincode': _pincodeController.text.trim(),
              'caste_category': _casteCategory,
              'user_type': _userType,
              'cooperative_role': _cooperativeRole,
            },
          },
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(authProvider.errorMessage ?? 'Failed to send OTP'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Widget _buildLabel(String text, {bool required = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Text(
            text,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          if (required)
            const Text(
              ' *',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: AppColors.error,
              ),
            ),
        ],
      ),
    );
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
        title: const Text('Create Account'),
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(24.0),
            children: [
              const Text(
                'Create Account',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Register to track your grievances and save profile info',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w400,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 32),
              
              // Phone Number (Display Only)
              _buildLabel('Phone Number', required: true),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.phone, size: 20, color: AppColors.textSecondary),
                    const SizedBox(width: 12),
                    Text(
                      widget.phoneNumber,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Full Name
              _buildLabel('Full Name', required: true),
              TextFormField(
                controller: _fullNameController,
                decoration: const InputDecoration(
                  hintText: 'Enter your full name',
                  prefixIcon: Icon(Icons.person_outline),
                ),
                textCapitalization: TextCapitalization.words,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your full name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // State
              _buildLabel('State', required: true),
              TextFormField(
                controller: _stateController,
                decoration: const InputDecoration(
                  hintText: 'e.g. Maharashtra',
                  prefixIcon: Icon(Icons.location_on_outlined),
                ),
                textCapitalization: TextCapitalization.words,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your state';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // District
              _buildLabel('District', required: true),
              TextFormField(
                controller: _districtController,
                decoration: const InputDecoration(
                  hintText: 'e.g. Nagpur',
                  prefixIcon: Icon(Icons.location_city_outlined),
                ),
                textCapitalization: TextCapitalization.words,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your district';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // Village or Town
              _buildLabel('Village / Town', required: true),
              TextFormField(
                controller: _villageController,
                decoration: const InputDecoration(
                  hintText: 'Enter your village or town',
                  prefixIcon: Icon(Icons.home_outlined),
                ),
                textCapitalization: TextCapitalization.words,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your village or town';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // Address
              _buildLabel('Address', required: true),
              TextFormField(
                controller: _addressController,
                decoration: const InputDecoration(
                  hintText: 'Enter your complete address',
                  prefixIcon: Icon(Icons.location_searching_outlined),
                ),
                maxLines: 2,
                textCapitalization: TextCapitalization.sentences,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your address';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // Pincode
              _buildLabel('Pincode', required: true),
              TextFormField(
                controller: _pincodeController,
                decoration: const InputDecoration(
                  hintText: 'Enter 6-digit pincode',
                  prefixIcon: Icon(Icons.pin_drop_outlined),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(6),
                ],
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter your pincode';
                  }
                  if (value.length != 6) {
                    return 'Please enter a valid 6-digit pincode';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),

              // Caste Category
              _buildLabel('Caste Category', required: true),
              DropdownButtonFormField<String>(
                value: _casteCategory,
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.category_outlined),
                ),
                items: const [
                  DropdownMenuItem(value: 'GENERAL', child: Text('General')),
                  DropdownMenuItem(value: 'OBC', child: Text('OBC')),
                  DropdownMenuItem(value: 'SC', child: Text('SC')),
                  DropdownMenuItem(value: 'ST', child: Text('ST')),
                  DropdownMenuItem(value: 'EWS', child: Text('EWS')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _casteCategory = value);
                  }
                },
              ),
              const SizedBox(height: 20),

              // User Type
              _buildLabel('I am a', required: true),
              DropdownButtonFormField<String>(
                value: _userType,
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.work_outline),
                ),
                items: const [
                  DropdownMenuItem(value: 'FARMER', child: Text('Farmer')),
                  DropdownMenuItem(value: 'PACS_MEMBER', child: Text('PACS Member')),
                  DropdownMenuItem(value: 'PACS_OFFICIAL', child: Text('PACS Official')),
                  DropdownMenuItem(value: 'COOPERATIVE_MEMBER', child: Text('Cooperative Member')),
                  DropdownMenuItem(value: 'COOPERATIVE_OFFICIAL', child: Text('Cooperative Official')),
                  DropdownMenuItem(value: 'GOVERNMENT_OFFICIAL', child: Text('Government Official')),
                  DropdownMenuItem(value: 'OTHER', child: Text('Other')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _userType = value);
                  }
                },
              ),
              const SizedBox(height: 20),

              // Cooperative Role
              _buildLabel('Cooperative Role', required: true),
              DropdownButtonFormField<String>(
                value: _cooperativeRole,
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.group_outlined),
                ),
                items: const [
                  DropdownMenuItem(value: 'MEMBER', child: Text('Member')),
                  DropdownMenuItem(value: 'BOARD_MEMBER', child: Text('Board Member')),
                  DropdownMenuItem(value: 'SECRETARY', child: Text('Secretary')),
                  DropdownMenuItem(value: 'CHAIRMAN', child: Text('Chairman')),
                  DropdownMenuItem(value: 'TREASURER', child: Text('Treasurer')),
                  DropdownMenuItem(value: 'MANAGER', child: Text('Manager')),
                  DropdownMenuItem(value: 'STAFF', child: Text('Staff')),
                  DropdownMenuItem(value: 'NOT_APPLICABLE', child: Text('Not Applicable')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _cooperativeRole = value);
                  }
                },
              ),
              const SizedBox(height: 32),

              // Continue button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _requestOtp,
                  child: _isLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Text('Continue with OTP'),
                            SizedBox(width: 8),
                            Icon(Icons.arrow_forward, size: 20),
                          ],
                        ),
                ),
              ),
              const SizedBox(height: 16),

              // Info message
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AppColors.primaryLight.withOpacity(0.3),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.info_outline,
                      size: 20,
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'We will send you a one-time password to verify your number and complete registration.',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: AppColors.textSecondary,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}
