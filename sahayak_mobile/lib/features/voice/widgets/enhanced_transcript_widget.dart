import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/theme/app_colors.dart';

/// Enhanced transcript widget with citations, links, and proper styling
class EnhancedTranscriptWidget extends StatelessWidget {
  final List<Map<String, dynamic>> transcript;
  final ScrollController scrollController;

  const EnhancedTranscriptWidget({
    super.key,
    required this.transcript,
    required this.scrollController,
  });

  @override
  Widget build(BuildContext context) {
    if (transcript.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFFF3F4F6),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.chat_outlined,
                size: 48,
                color: Color(0xFF9CA3AF),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'No conversation yet',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Color(0xFF6B7280),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Start speaking to see the transcript',
              style: TextStyle(
                fontSize: 14,
                color: Color(0xFF9CA3AF),
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: scrollController,
      reverse: true, // Scroll upwards like chat
      padding: const EdgeInsets.all(16),
      itemCount: transcript.length,
      itemBuilder: (context, index) {
        final reversedIndex = transcript.length - 1 - index;
        final entry = transcript[reversedIndex];
        final isUser = entry['speaker'] == 'user';
        final text = entry['text'] ?? '';
        final citations = entry['citations'] as Map<String, dynamic>?;

        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Align(
            alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
            child: Column(
              crossAxisAlignment:
                  isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                // Message bubble
                Container(
                  constraints: BoxConstraints(
                    maxWidth: MediaQuery.of(context).size.width * 0.80,
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    gradient: isUser
                        ? LinearGradient(
                            colors: [
                              const Color(0xFF3B82F6),
                              const Color(0xFF2563EB),
                            ],
                          )
                        : null,
                    color: isUser ? null : const Color(0xFFF3F4F6),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(isUser ? 16 : 4),
                      bottomRight: Radius.circular(isUser ? 4 : 16),
                    ),
                    boxShadow: isUser
                        ? [
                            BoxShadow(
                              color: const Color(0xFF3B82F6).withOpacity(0.3),
                              offset: const Offset(0, 2),
                              blurRadius: 8,
                            ),
                          ]
                        : null,
                  ),
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: isUser ? Colors.white : const Color(0xFF1F2937),
                      height: 1.4,
                    ),
                  ),
                ),

                // Citations section for agent messages
                if (!isUser && citations != null && citations['sources'] != null)
                  _buildCitationsSection(context, citations),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildCitationsSection(
      BuildContext context, Map<String, dynamic> citations) {
    final sources = citations['sources'] as List<dynamic>?;
    if (sources == null || sources.isEmpty) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.80,
      ),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: const Color(0xFF3B82F6).withOpacity(0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.verified_outlined,
                size: 16,
                color: const Color(0xFF3B82F6),
              ),
              const SizedBox(width: 6),
              const Text(
                'Official Sources',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF3B82F6),
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...sources.map((source) {
            if (source is! Map) return const SizedBox.shrink();
            final sourceMap = Map<String, dynamic>.from(source);
            return _buildSourceLink(context, sourceMap);
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildSourceLink(BuildContext context, Map<String, dynamic> source) {
    final name = source['name'] ?? 'Source';
    final url = source['url'];
    final freshness = source['freshness_status'];

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: InkWell(
        onTap: url != null
            ? () async {
                final uri = Uri.tryParse(url);
                if (uri != null && await canLaunchUrl(uri)) {
                  await launchUrl(uri, mode: LaunchMode.externalApplication);
                }
              }
            : null,
        child: Row(
          children: [
            Icon(
              Icons.insert_link_rounded,
              size: 14,
              color: const Color(0xFF3B82F6),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                name,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF3B82F6),
                  decoration: TextDecoration.underline,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (freshness == 'FRESH')
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'Current',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF10B981),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
