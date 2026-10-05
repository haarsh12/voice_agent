import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/knowledge_provider.dart';
import '../../../shared/widgets/error_widget.dart';
import '../../../shared/widgets/empty_state_widget.dart';
import '../../../shared/widgets/shimmer_loading.dart';

class KnowledgeBaseScreen extends StatefulWidget {
  const KnowledgeBaseScreen({super.key});

  @override
  State<KnowledgeBaseScreen> createState() => _KnowledgeBaseScreenState();
}

class _KnowledgeBaseScreenState extends State<KnowledgeBaseScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _scrollController.addListener(_onScroll);
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<KnowledgeProvider>();
      provider.fetchKnowledgeBase();
      provider.fetchDocuments();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_tabController.index == 1 &&
        _scrollController.position.pixels >=
            _scrollController.position.maxScrollExtent - 200) {
      context.read<KnowledgeProvider>().loadMoreDocuments();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Knowledge Base'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Documents'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOverviewTab(),
          _buildDocumentsTab(),
        ],
      ),
    );
  }

  Widget _buildOverviewTab() {
    final knowledgeProvider = context.watch<KnowledgeProvider>();

    if (knowledgeProvider.isLoading && knowledgeProvider.knowledgeBase == null) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          ShimmerCard(height: 120),
          SizedBox(height: 12),
          ShimmerCard(height: 120),
          SizedBox(height: 12),
          ShimmerCard(height: 120),
          SizedBox(height: 12),
          ShimmerCard(height: 120),
        ],
      );
    }

    if (knowledgeProvider.errorMessage != null && knowledgeProvider.knowledgeBase == null) {
      return ErrorStateWidget(
        message: knowledgeProvider.errorMessage!,
        onRetry: () => knowledgeProvider.fetchKnowledgeBase(forceRefresh: true),
      );
    }

    final knowledge = knowledgeProvider.knowledgeBase;
    if (knowledge == null) {
      return const Center(child: Text('No data available'));
    }

    return RefreshIndicator(
      onRefresh: () => knowledgeProvider.fetchKnowledgeBase(forceRefresh: true),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildStatCard(
            'Official Sources',
            knowledge['official_sources']?.toString() ?? '0',
            Icons.verified,
            AppColors.primary,
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            'Current Documents',
            knowledge['current_documents']?.toString() ?? '0',
            Icons.description,
            AppColors.info,
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            'Knowledge Chunks',
            knowledge['knowledge_chunks']?.toString() ?? '0',
            Icons.auto_awesome,
            AppColors.success,
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            'Vector Index',
            knowledge['vector_index'] ?? 'Ready',
            Icons.storage,
            AppColors.secondary,
          ),
          const SizedBox(height: 24),
          const Text(
            'About Knowledge Base',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.infoLight,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.info.withOpacity(0.2)),
            ),
            child: const Text(
              'The knowledge base contains verified official sources, current document records, and extracted knowledge chunks. All information is regularly updated to ensure accuracy and relevance.',
              style: TextStyle(
                fontSize: 15,
                color: AppColors.textSecondary,
                height: 1.6,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDocumentsTab() {
    final provider = context.watch<KnowledgeProvider>();

    if (provider.isLoading && provider.documents.isEmpty) {
      return ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: 8,
        separatorBuilder: (context, index) => const SizedBox(height: 12),
        itemBuilder: (context, index) => const ShimmerKnowledgeItem(),
      );
    }

    if (provider.errorMessage != null && provider.documents.isEmpty) {
      return ErrorStateWidget(
        message: provider.errorMessage!,
        onRetry: () => provider.fetchDocuments(forceRefresh: true),
      );
    }

    if (provider.documents.isEmpty) {
      return const EmptyStateWidget(
        icon: Icons.description_outlined,
        title: 'No documents found',
        message: 'Knowledge documents will appear here',
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.fetchDocuments(forceRefresh: true),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        itemCount: provider.documents.length + (provider.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == provider.documents.length) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Center(
                child: provider.isLoadingMore
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const SizedBox.shrink(),
              ),
            );
          }

          final doc = provider.documents[index];

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: const BorderSide(color: AppColors.border),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: _getDocumentTypeColor(doc.type).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      _getDocumentTypeIcon(doc.type),
                      color: _getDocumentTypeColor(doc.type),
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          doc.title.contains('%') ? Uri.decodeComponent(doc.title) : doc.title,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textPrimary,
                            height: 1.3,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            if (doc.type != null) ...[
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 3,
                                ),
                                decoration: BoxDecoration(
                                  color: _getDocumentTypeColor(doc.type).withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  doc.type!,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: _getDocumentTypeColor(doc.type),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                            ],
                            if (doc.chunks != null) ...[
                              Icon(
                                Icons.auto_awesome,
                                size: 14,
                                color: AppColors.textTertiary,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${doc.chunks} chunks',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textTertiary,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Color _getDocumentTypeColor(String? type) {
    if (type == null) return AppColors.primary;
    final typeLower = type.toLowerCase();
    
    if (typeLower.contains('pdf')) return AppColors.error;
    if (typeLower.contains('web') || typeLower.contains('html')) return AppColors.info;
    if (typeLower.contains('doc')) return AppColors.primary;
    return AppColors.secondary;
  }

  IconData _getDocumentTypeIcon(String? type) {
    if (type == null) return Icons.description;
    final typeLower = type.toLowerCase();
    
    if (typeLower.contains('pdf')) return Icons.picture_as_pdf;
    if (typeLower.contains('web') || typeLower.contains('html')) return Icons.language;
    if (typeLower.contains('doc')) return Icons.article;
    return Icons.description;
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 28),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppColors.textSecondary,
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
