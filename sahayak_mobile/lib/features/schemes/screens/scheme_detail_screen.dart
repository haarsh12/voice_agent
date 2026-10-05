import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/schemes_provider.dart';
import '../models/scheme_model.dart';
import '../../../shared/widgets/premium_button.dart';

class SchemeDetailScreen extends StatefulWidget {
  final String schemeId;

  const SchemeDetailScreen({
    super.key,
    required this.schemeId,
  });

  @override
  State<SchemeDetailScreen> createState() => _SchemeDetailScreenState();
}

class _SchemeDetailScreenState extends State<SchemeDetailScreen> {
  SchemeModel? _scheme;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadScheme();
  }

  Future<void> _loadScheme() async {
    try {
      final provider = context.read<SchemesProvider>();
      final scheme = await provider.fetchSchemeById(widget.schemeId);
      if (mounted) {
        setState(() {
          _scheme = scheme;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Scheme Details'),
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.ink))
          : _error != null || _scheme == null
              ? Center(child: Text(_error ?? 'Scheme not found'))
              : _buildBody(_scheme!),
    );
  }

  Widget _buildBody(SchemeModel scheme) {
    // Try to find official URL from sources
    String? officialUrl = scheme.metadata?['official_url']?.toString();
    if (officialUrl == null && scheme.sources?.isNotEmpty == true) {
      final firstUrl = scheme.sources!.first['url']?.toString();
      if (firstUrl != null && firstUrl.startsWith('http')) {
        officialUrl = firstUrl;
      }
    }

    return Stack(
      children: [
        SingleChildScrollView(
          padding: const EdgeInsets.only(left: 24, right: 24, top: 16, bottom: 120),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Category & type tags
              Row(
                children: [
                  if (scheme.type != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceAlt,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        scheme.type!.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  if (scheme.type != null && scheme.category != null)
                    const SizedBox(width: 8),
                  if (scheme.category != null)
                    Flexible(
                      child: Text(
                        scheme.category!.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.5,
                          color: AppColors.textSecondary,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 16),

              // Title
              Text(
                scheme.title,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                  height: 1.2,
                ),
              ),

              // Acronym
              if (scheme.acronym != null) ...[
                const SizedBox(height: 8),
                Text(
                  scheme.acronym!,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],

              const SizedBox(height: 20),

              // Tags: geography, status
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (scheme.geography != null)
                    _buildTag(Icons.public_rounded, scheme.geography!),
                  if (scheme.status != null && scheme.status != 'UNKNOWN')
                    _buildTag(Icons.circle, scheme.status!),
                ],
              ),

              // Beneficiaries
              if (scheme.beneficiaries != null && scheme.beneficiaries!.isNotEmpty) ...[
                const SizedBox(height: 24),
                _sectionLabel('WHO CAN BENEFIT?'),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: scheme.beneficiaries!.map((b) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceAlt,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      _formatBeneficiary(b),
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  )).toList(),
                ),
              ],

              // Content sections from nested `data` object
              if (scheme.description != null) ...[
                const SizedBox(height: 32),
                _buildContentBox('DESCRIPTION', scheme.description!),
              ],
              if (scheme.data?['objective'] != null) ...[
                const SizedBox(height: 16),
                _buildContentBox('OBJECTIVE', scheme.data!['objective'].toString()),
              ],
              if (scheme.data?['benefits'] != null) ...[
                const SizedBox(height: 16),
                _buildContentBox('BENEFITS', scheme.data!['benefits'].toString()),
              ],
              if (scheme.data?['eligibility'] != null) ...[
                const SizedBox(height: 16),
                _buildContentBox('ELIGIBILITY', scheme.data!['eligibility'].toString()),
              ],
              if (scheme.data?['application_process'] != null) ...[
                const SizedBox(height: 16),
                _buildContentBox('HOW TO APPLY', scheme.data!['application_process'].toString()),
              ],
              if (scheme.data?['required_documents'] != null) ...[
                const SizedBox(height: 16),
                _buildContentBox('REQUIRED DOCUMENTS', scheme.data!['required_documents'].toString()),
              ],

              // Sources
              if (scheme.sources != null && scheme.sources!.isNotEmpty) ...[
                const SizedBox(height: 24),
                _sectionLabel('SOURCES'),
                const SizedBox(height: 12),
                ...scheme.sources!.take(3).map((s) {
                  final title = s['title']?.toString() ?? '';
                  final url = s['url']?.toString() ?? '';
                  final section = s['relevant_section']?.toString();
                  if (url.isEmpty) return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: GestureDetector(
                      onTap: () async {
                        final uri = Uri.tryParse(url);
                        if (uri != null && await canLaunchUrl(uri)) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      },
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceAlt,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.link_rounded, size: 16, color: AppColors.textSecondary),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  if (title.isNotEmpty)
                                    Text(
                                      title,
                                      style: const TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.ink,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  if (section != null)
                                    Text(
                                      section,
                                      style: const TextStyle(
                                        fontSize: 11,
                                        color: AppColors.textSecondary,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                ],
                              ),
                            ),
                            const Icon(Icons.open_in_new_rounded, size: 14, color: AppColors.textSecondary),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ],
          ),
        ),

        // Floating action buttons
        Positioned(
          bottom: 24,
          left: 24,
          child: officialUrl != null
              ? GestureDetector(
                  onTap: () async {
                    final uri = Uri.tryParse(officialUrl!);
                    if (uri != null && await canLaunchUrl(uri)) {
                      await launchUrl(uri, mode: LaunchMode.externalApplication);
                    }
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.border),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.open_in_new_rounded, size: 16, color: AppColors.ink),
                        SizedBox(width: 8),
                        Text(
                          'Official Portal',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppColors.ink,
                          ),
                        ),
                      ],
                    ),
                  ),
                )
              : const SizedBox.shrink(),
        ),
        Positioned(
          bottom: 24,
          right: 24,
          child: PremiumButton(
            text: 'Ask Sahayak',
            onPressed: () {},
            style: PremiumButtonStyle.primary,
            size: PremiumButtonSize.medium,
          ),
        ),
      ],
    );
  }

  String _formatBeneficiary(String b) {
    return b.replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : w)
        .join(' ');
  }

  Widget _sectionLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: AppColors.textSecondary,
        letterSpacing: 0.5,
      ),
    );
  }

  Widget _buildTag(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surfaceAlt,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: AppColors.textSecondary),
          const SizedBox(width: 6),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContentBox(String title, String content) {
    // Trim excessively long content
    final trimmed = content.length > 800 ? '${content.substring(0, 800)}…' : content;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceAlt,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: AppColors.textSecondary,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            trimmed,
            style: const TextStyle(
              fontSize: 14,
              color: AppColors.textPrimary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
