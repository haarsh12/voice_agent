import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/services_provider.dart';
import '../../../shared/widgets/error_widget.dart';
import '../../../shared/widgets/empty_state_widget.dart';
import '../../../shared/widgets/shimmer_loading.dart';

/// Services screen showing all available services with enhanced grid
class ServicesScreen extends StatefulWidget {
  const ServicesScreen({super.key});

  @override
  State<ServicesScreen> createState() => _ServicesScreenState();
}

class _ServicesScreenState extends State<ServicesScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ServicesProvider>().fetchServices();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      context.read<ServicesProvider>().loadMoreServices();
    }
  }

  @override
  Widget build(BuildContext context) {
    final servicesProvider = context.watch<ServicesProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Services'),
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search services...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          servicesProvider.searchServices('');
                          setState(() {});
                        },
                      )
                    : null,
              ),
              onChanged: (value) {
                servicesProvider.searchServices(value);
                setState(() {});
              },
            ),
          ),
          
          // Services list
          Expanded(
            child: _buildContent(servicesProvider),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(ServicesProvider provider) {
    // Show shimmer loading for initial load
    if (provider.isLoading && provider.services.isEmpty) {
      return GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.0,
        ),
        itemCount: 6,
        itemBuilder: (context, index) => const ShimmerServiceCard(),
      );
    }

    if (provider.errorMessage != null && provider.services.isEmpty) {
      return ErrorStateWidget(
        message: provider.errorMessage!,
        onRetry: () => provider.fetchServices(forceRefresh: true),
      );
    }

    if (provider.services.isEmpty) {
      return const EmptyStateWidget(
        icon: Icons.business_center_outlined,
        title: 'No services found',
        message: 'Try adjusting your search',
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.fetchServices(forceRefresh: true),
      child: GridView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.0,
        ),
        itemCount: provider.services.length + (provider.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          // Show loading indicator at the end
          if (index == provider.services.length) {
            return Center(
              child: provider.isLoadingMore
                  ? const Padding(
                      padding: EdgeInsets.all(16),
                      child: SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  : const SizedBox.shrink(),
            );
          }

          final service = provider.services[index];
          final categoryColor = _getCategoryColor(service.category);
          
          return InkWell(
            onTap: () => context.push('/service/${service.id}'),
            borderRadius: BorderRadius.circular(12),
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: categoryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      _getServiceIcon(service.category),
                      size: 28,
                      color: categoryColor,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    service.name,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                      height: 1.3,
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (service.category != null) ...[
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: categoryColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        service.category!,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          color: categoryColor,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Color _getCategoryColor(String? category) {
    if (category == null) return AppColors.primary;
    
    final categoryLower = category.toLowerCase();
    if (categoryLower.contains('cooperative')) {
      return AppColors.primary;
    } else if (categoryLower.contains('insurance') || categoryLower.contains('pmfby')) {
      return AppColors.success;
    } else if (categoryLower.contains('law') || categoryLower.contains('legal')) {
      return AppColors.secondary;
    } else if (categoryLower.contains('financial') || categoryLower.contains('finance')) {
      return AppColors.finance;
    } else if (categoryLower.contains('grievance')) {
      return AppColors.error;
    } else if (categoryLower.contains('document')) {
      return AppColors.info;
    } else {
      return AppColors.primary;
    }
  }

  IconData _getServiceIcon(String? category) {
    switch (category?.toLowerCase()) {
      case 'cooperative':
        return Icons.business;
      case 'pmfby':
      case 'insurance':
        return Icons.security;
      case 'laws':
      case 'legal':
        return Icons.gavel;
      case 'financial':
        return Icons.account_balance;
      case 'grievance':
        return Icons.report_problem;
      case 'documents':
        return Icons.description;
      default:
        return Icons.business_center;
    }
  }
}
