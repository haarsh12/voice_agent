import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/grievances_provider.dart';

class CreateGrievanceScreen extends StatefulWidget {
  const CreateGrievanceScreen({super.key});

  @override
  State<CreateGrievanceScreen> createState() => _CreateGrievanceScreenState();
}

class _CreateGrievanceScreenState extends State<CreateGrievanceScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController(); // subject
  final _descriptionController = TextEditingController(); // description
  final _orgController = TextEditingController(); // organization
  final _stateController = TextEditingController(); // state
  final _districtController = TextEditingController(); // district
  final _amountController = TextEditingController(); // amount_description
  final _referenceController = TextEditingController(); // prior_reference
  
  String? _category = 'OTHER_GOVERNMENT';
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _orgController.dispose();
    _stateController.dispose();
    _districtController.dispose();
    _amountController.dispose();
    _referenceController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final grievancesProvider = context.read<GrievancesProvider>();
    final success = await grievancesProvider.createGrievance({
      'subject': _titleController.text.trim(),
      'description': _descriptionController.text.trim(),
      'category': _category,
      if (_orgController.text.trim().isNotEmpty) 'organization': _orgController.text.trim(),
      if (_stateController.text.trim().isNotEmpty) 'state': _stateController.text.trim(),
      if (_districtController.text.trim().isNotEmpty) 'district': _districtController.text.trim(),
      if (_amountController.text.trim().isNotEmpty) 'amount_description': _amountController.text.trim(),
      if (_referenceController.text.trim().isNotEmpty) 'prior_reference': _referenceController.text.trim(),
    });

    if (mounted) {
      setState(() => _isLoading = false);

      if (success) {
        context.pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Grievance created successfully'),
            backgroundColor: AppColors.success,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(grievancesProvider.errorMessage ?? 'Failed to create grievance'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: AppColors.textPrimary,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Create Grievance'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            _buildLabel('What is a short title for this issue?'),
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(hintText: 'For example: PACS payment not received'),
              validator: (value) => (value == null || value.trim().isEmpty) ? 'Please enter a title' : null,
            ),
            const SizedBox(height: 20),
            
            _buildLabel('Issue type'),
            DropdownButtonFormField<String>(
              value: _category,
              decoration: const InputDecoration(),
              items: const [
                DropdownMenuItem(value: 'PACS_FINANCIAL', child: Text('PACS Financial Issue')),
                DropdownMenuItem(value: 'PACS_OPERATIONAL', child: Text('PACS Operational Issue')),
                DropdownMenuItem(value: 'REGISTRAR_ISSUE', child: Text('Registrar Issue')),
                DropdownMenuItem(value: 'OTHER_GOVERNMENT', child: Text('Other government service issue')),
                DropdownMenuItem(value: 'GENERAL_INQUIRY', child: Text('General Inquiry')),
              ],
              onChanged: (val) {
                if (val != null) setState(() => _category = val);
              },
            ),
            const SizedBox(height: 20),

            _buildLabel('PACS or organisation involved'),
            TextFormField(
              controller: _orgController,
              decoration: const InputDecoration(hintText: 'Name, if known'),
            ),
            const SizedBox(height: 20),

            _buildLabel('What happened?'),
            TextFormField(
              controller: _descriptionController,
              decoration: const InputDecoration(hintText: 'Describe the facts, relevant dates and the help you need.'),
              maxLines: 4,
              validator: (value) => (value == null || value.trim().isEmpty) ? 'Please enter a description' : null,
            ),
            const SizedBox(height: 20),

            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildLabel('State'),
                      TextFormField(
                        controller: _stateController,
                        decoration: const InputDecoration(hintText: 'e.g. Maharashtra'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildLabel('District'),
                      TextFormField(
                        controller: _districtController,
                        decoration: const InputDecoration(hintText: 'e.g. Nagpur'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            _buildLabel('Amount, if relevant'),
            TextFormField(
              controller: _amountController,
              decoration: const InputDecoration(hintText: 'For example: about ₹5,000'),
            ),
            const SizedBox(height: 20),

            _buildLabel('Earlier complaint number'),
            TextFormField(
              controller: _referenceController,
              decoration: const InputDecoration(hintText: 'If you have one'),
            ),
            const SizedBox(height: 32),

            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Submit Grievance'),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
