import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/voice_provider.dart';

/// Transcript view showing conversation history
class TranscriptView extends StatelessWidget {
  const TranscriptView({super.key});

  @override
  Widget build(BuildContext context) {
    final voiceProvider = context.watch<VoiceProvider>();
    final transcript = voiceProvider.transcript;

    if (transcript.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chat_bubble_outline,
              size: 64,
              color: AppColors.textTertiary,
            ),
            const SizedBox(height: 16),
            Text(
              'No conversation yet',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Start a conversation to see the transcript',
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textTertiary,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        // Header with clear button
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.surfaceVariant,
            border: Border(
              bottom: BorderSide(color: AppColors.divider),
            ),
          ),
          child: Row(
            children: [
              const Text(
                'Live Transcript',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: () {
                  voiceProvider.clearTranscript();
                },
                icon: const Icon(Icons.clear_all, size: 18),
                label: const Text('Clear'),
              ),
            ],
          ),
        ),
        
        // Transcript messages
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            reverse: true,
            itemCount: transcript.length,
            itemBuilder: (context, index) {
              final message = transcript[transcript.length - 1 - index];
              return _TranscriptMessage(
                speaker: message['speaker'] ?? 'user',
                text: message['text'] ?? '',
                timestamp: message['timestamp'],
              );
            },
          ),
        ),
      ],
    );
  }
}

class _TranscriptMessage extends StatelessWidget {
  final String speaker;
  final String text;
  final String? timestamp;

  const _TranscriptMessage({
    required this.speaker,
    required this.text,
    this.timestamp,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = speaker == 'user';
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            _buildAvatar(),
            const SizedBox(width: 12),
          ],
          
          Flexible(
            child: Column(
              crossAxisAlignment:
                  isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: isUser ? AppColors.primary : AppColors.surfaceVariant,
                    borderRadius: BorderRadius.circular(16).copyWith(
                      topLeft: isUser ? const Radius.circular(16) : Radius.zero,
                      topRight: isUser ? Radius.zero : const Radius.circular(16),
                    ),
                  ),
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w400,
                      color: isUser ? Colors.white : AppColors.textPrimary,
                      height: 1.4,
                    ),
                  ),
                ),
                if (timestamp != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    _formatTime(timestamp!),
                    style: TextStyle(
                      fontSize: 11,
                      color: AppColors.textTertiary,
                    ),
                  ),
                ],
              ],
            ),
          ),
          
          if (isUser) ...[
            const SizedBox(width: 12),
            _buildAvatar(),
          ],
        ],
      ),
    );
  }

  Widget _buildAvatar() {
    final isUser = speaker == 'user';
    
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isUser ? AppColors.primary.withOpacity(0.1) : AppColors.secondary.withOpacity(0.1),
      ),
      child: Icon(
        isUser ? Icons.person : Icons.smart_toy,
        size: 20,
        color: isUser ? AppColors.primary : AppColors.secondary,
      ),
    );
  }

  String _formatTime(String isoString) {
    try {
      final dateTime = DateTime.parse(isoString);
      return DateFormat.jm().format(dateTime);
    } catch (e) {
      return '';
    }
  }
}
