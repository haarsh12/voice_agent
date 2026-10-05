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
  final _localityController = TextEditingController(); // locality (village/town)
  final _amountController = TextEditingController(); // amount_description
  final _referenceController = TextEditingController(); // prior_reference
  
  String? _category = 'OTHER_GOVERNMENT';
  String? _hasContactedOrg; // null, 'yes', or 'no'
  DateTime? _incidentDate;
  bool _isLoading = false;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _orgController.dispose();
    _stateController.dispose();
    _districtController.dispose();
    _localityController.dispose();
    _amountController.dispose();
    _referenceController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final grievancesProvider = context.read<GrievancesProvider>();
    
    // Prepare grievance data matching website fields
    final grievanceData = <String, dynamic>{
      'subject': _titleController.text.trim(),
      'description': _descriptionController.text.trim(),
      'category': _category,
    };
    
    // Add optional fields only if they have values
    if (_orgController.text.trim().isNotEmpty) {
      grievanceData['organization'] = _orgController.text.trim();
    }
    if (_stateController.text.trim().isNotEmpty) {
      grievanceData['state'] = _stateController.text.trim();
    }
    if (_districtController.text.trim().isNotEmpty) {
      grievanceData['district'] = _districtController.text.trim();
    }
    if (_localityController.text.trim().isNotEmpty) {
      grievanceData['locality'] = _localityController.text.trim();
    }
    if (_incidentDate != null) {
      grievanceData['incident_date'] = _incidentDate!.toIso8601String().split('T')[0];
    }
    if (_amountController.text.trim().isNotEmpty) {
      grievanceData['amount_description'] = _amountController.text.trim();
    }
    if (_hasContactedOrg != null) {
      grievanceData['has_contacted_organization'] = _hasContactedOrg == 'yes';
    }
    if (_referenceController.text.trim().isNotEmpty) {
      grievanceData['prior_reference'] = _referenceController.text.trim();
    }
    
    final success = await grievancesProvider.createGrievance(grievanceData);

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
                DropdownMenuItem(value: 'PACS_ISSUE', child: Text('PACS issue')),
                DropdownMenuItem(value: 'COOPERATIVE_SOCIETY', child: Text('Cooperative society issue')),
                DropdownMenuItem(value: 'PAYMENT', child: Text('Payment issue')),
                DropdownMenuItem(value: 'LOAN', child: Text('Loan or credit issue')),
                DropdownMenuItem(value: 'INSURANCE_CLAIM', child: Text('Insurance or claim issue')),
                DropdownMenuItem(value: 'GOVERNMENT_SCHEME', child: Text('Government scheme issue')),
                DropdownMenuItem(value: 'AGRICULTURE_SERVICE', child: Text('Agriculture service issue')),
                DropdownMenuItem(value: 'FINANCIAL_SERVICE', child: Text('Financial service issue')),
                DropdownMenuItem(value: 'DOCUMENT_CERTIFICATE', child: Text('Document or certificate issue')),
                DropdownMenuItem(value: 'ADMINISTRATIVE', child: Text('Administrative issue')),
                DropdownMenuItem(value: 'OTHER_GOVERNMENT', child: Text('Other government service issue')),
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

            _buildLabel('Village / Town / Locality'),
            TextFormField(
              controller: _localityController,
              decoration: const InputDecoration(hintText: 'Your locality, if known'),
            ),
            const SizedBox(height: 20),

            _buildLabel('When did this happen?'),
            InkWell(
              onTap: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _incidentDate ?? DateTime.now(),
                  firstDate: DateTime(2000),
                  lastDate: DateTime.now(),
                );
                if (picked != null) {
                  setState(() => _incidentDate = picked);
                }
              },
              child: InputDecorator(
                decoration: const InputDecoration(
                  hintText: 'Select date',
                  suffixIcon: Icon(Icons.calendar_today),
                ),
                child: Text(
                  _incidentDate == null
                      ? 'Tap to select date'
                      : '${_incidentDate!.day}/${_incidentDate!.month}/${_incidentDate!.year}',
                  style: TextStyle(
                    color: _incidentDate == null 
                        ? AppColors.textSecondary 
                        : AppColors.textPrimary,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),

            _buildLabel('Amount, if relevant'),
            TextFormField(
              controller: _amountController,
              decoration: const InputDecoration(hintText: 'For example: about ₹5,000'),
            ),
            const SizedBox(height: 20),

            _buildLabel('Have you already contacted them?'),
            DropdownButtonFormField<String>(
              value: _hasContactedOrg,
              decoration: const InputDecoration(),
              items: const [
                DropdownMenuItem(value: null, child: Text('I do not know / not applicable')),
                DropdownMenuItem(value: 'yes', child: Text('Yes')),
                DropdownMenuItem(value: 'no', child: Text('No')),
              ],
              onChanged: (val) {
                setState(() => _hasContactedOrg = val);
              },
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
            const SizedBox(height: 16),

            // Info note matching website
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
                      'Only share facts you are comfortable providing. Do not include passwords, PINs, OTPs, or bank card details. Supporting files are never uploaded automatically.',
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
    );
  }
}
