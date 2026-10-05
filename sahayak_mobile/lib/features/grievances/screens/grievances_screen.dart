import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/providers/auth_provider.dart' as import_auth;
import '../providers/grievances_provider.dart';
import '../../../shared/widgets/loading_widget.dart';
import '../../../shared/widgets/error_widget.dart';
import '../../../shared/widgets/empty_state_widget.dart';

class GrievancesScreen extends StatefulWidget {
  const GrievancesScreen({super.key});

  @override
  State<GrievancesScreen> createState() => _GrievancesScreenState();
}

class _GrievancesScreenState extends State<GrievancesScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<import_auth.AuthProvider>();
      if (auth.isAuthenticated) {
        context.read<GrievancesProvider>().fetchGrievances();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final grievancesProvider = context.watch<GrievancesProvider>();
    final authProvider = context.watch<import_auth.AuthProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('My Grievances'),
      ),
      body: authProvider.isGuest 
          ? const EmptyStateWidget(
              icon: Icons.login_rounded,
              title: 'Login Required',
              message: 'Please login to view and manage your grievances.',
            )
          : _buildContent(grievancesProvider),
      floatingActionButton: authProvider.isGuest ? null : FloatingActionButton.extended(
        onPressed: () {
          context.push('/grievances/create');
        },
        icon: const Icon(Icons.add),
        label: const Text('New Grievance'),
      ),
    );
  }

  Widget _buildContent(GrievancesProvider provider) {
    if (provider.isLoading) {
      return const LoadingWidget(message: 'Loading grievances...');
    }

    if (provider.errorMessage != null) {
      return ErrorStateWidget(
        message: provider.errorMessage!,
        onRetry: () => provider.fetchGrievances(),
      );
    }

    if (provider.grievances.isEmpty) {
      return const EmptyStateWidget(
        icon: Icons.report_outlined,
        title: 'No grievances yet',
        message: 'Create your first grievance to get started',
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.fetchGrievances(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: provider.grievances.length,
        itemBuilder: (context, index) {
          final grievance = provider.grievances[index];
          
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: InkWell(
              onTap: () => context.push('/grievances/${grievance.id}'),
              borderRadius: BorderRadius.circular(16),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            grievance.title,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: AppColors.textPrimary,
                            ),
                          ),
                        ),
                        _buildStatusChip(grievance.status),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      grievance.description,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.textSecondary,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color color;
    switch (status.toLowerCase()) {
      case 'resolved':
        color = AppColors.success;
        break;
      case 'in_progress':
        color = AppColors.warning;
        break;
      default:
        color = AppColors.textSecondary;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        status.replaceAll('_', ' ').toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
