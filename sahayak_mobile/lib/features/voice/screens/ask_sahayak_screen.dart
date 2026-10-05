import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/providers/language_provider.dart';
import '../../../shared/widgets/siri_wave_orb.dart';
import '../providers/voice_provider.dart';
import '../widgets/transcript_view.dart';

/// Ask Sahayak - Premium voice assistant screen with SiriWaveOrb animation
class AskSahayakScreen extends StatefulWidget {
  const AskSahayakScreen({super.key});

  @override
  State<AskSahayakScreen> createState() => _AskSahayakScreenState();
}

class _AskSahayakScreenState extends State<AskSahayakScreen>
    with SingleTickerProviderStateMixin {
  bool _showTranscript = false;
  double _audioLevel = 0.0;
  Timer? _audioLevelTimer;
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    );
    _fadeController.forward();
  }

  @override
  void dispose() {
    _audioLevelTimer?.cancel();
    _fadeController.dispose();
    super.dispose();
  }

  void _startAudioLevelAnimation() {
    _audioLevelTimer?.cancel();
    _audioLevelTimer = Timer.periodic(const Duration(milliseconds: 150), (_) {
      if (!mounted) return;
      setState(() {
        // Simulate audio level variation when connected
        _audioLevel = 0.3 + (0.4 * (DateTime.now().millisecond % 1000) / 1000);
      });
    });
  }

  void _stopAudioLevelAnimation() {
    _audioLevelTimer?.cancel();
    if (mounted) {
      setState(() => _audioLevel = 0.0);
    }
  }

  @override
  Widget build(BuildContext context) {
    final voiceProvider = context.watch<VoiceProvider>();
    
    // Manage audio animation based on connection state
    if (voiceProvider.isConnected && _audioLevelTimer == null) {
      _startAudioLevelAnimation();
    } else if (!voiceProvider.isConnected && _audioLevelTimer != null) {
      _stopAudioLevelAnimation();
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: AppColors.surface,
        title: const Text(
          'Ask Sahayak',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        actions: [
          IconButton(
            icon: Icon(
              _showTranscript ? Icons.mic_rounded : Icons.chat_bubble_rounded,
              color: _showTranscript ? AppColors.primary : AppColors.textSecondary,
            ),
            onPressed: () {
              HapticFeedback.lightImpact();
              setState(() => _showTranscript = !_showTranscript);
            },
            tooltip: _showTranscript ? 'Show Voice Mode' : 'Show Transcript',
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Language selector
            const _LanguageBar(),
            
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: _showTranscript
                    ? const TranscriptView()
                    : _VoiceAssistantView(
                        audioLevel: _audioLevel,
                        fadeAnimation: _fadeAnimation,
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LanguageBar extends StatelessWidget {
  const _LanguageBar();

  @override
  Widget build(BuildContext context) {
    final languageProvider = context.watch<LanguageProvider>();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(
          bottom: BorderSide(color: Color(0xFFE5DED1), width: 1),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: AppColors.greenPale,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.language_rounded,
              size: 18,
              color: AppColors.green,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  languageProvider.currentLanguageName,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.ink,
                  ),
                ),
                Text(
                  LanguageProvider.languageScriptNames[
                          languageProvider.currentLanguageCode] ??
                      '',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.muted,
                  ),
                ),
              ],
            ),
          ),
          TextButton.icon(
            onPressed: () => _showLanguageSelector(context),
            icon: const Icon(Icons.swap_horiz, size: 18),
            label: const Text('Change'),
            style: TextButton.styleFrom(
              foregroundColor: AppColors.green,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            ),
          ),
        ],
      ),
    );
  }

  void _showLanguageSelector(BuildContext context) {
    final languageProvider = context.read<LanguageProvider>();

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.greenPale,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.language_rounded,
                        color: AppColors.green,
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Text(
                      'Select Language',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                ...LanguageProvider.supportedLocales.map((locale) {
                  final code = locale.languageCode;
                  final isSelected =
                      languageProvider.currentLanguageCode == code;

                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? AppColors.greenPale
                          : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isSelected
                            ? AppColors.green
                            : const Color(0xFFE5E5E5),
                        width: isSelected ? 2 : 1,
                      ),
                    ),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 4,
                      ),
                      leading: Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppColors.green
                              : AppColors.subtle,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          isSelected
                              ? Icons.check_rounded
                              : Icons.language_rounded,
                          color: isSelected
                              ? Colors.white
                              : AppColors.muted,
                          size: 20,
                        ),
                      ),
                      title: Text(
                        LanguageProvider.languageNames[code] ?? '',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight:
                              isSelected ? FontWeight.w600 : FontWeight.w500,
                          color: isSelected
                              ? AppColors.green
                              : AppColors.ink,
                        ),
                      ),
                      subtitle: Text(
                        LanguageProvider.languageScriptNames[code] ?? '',
                        style: TextStyle(
                          fontSize: 13,
                          color: isSelected
                              ? AppColors.green.withOpacity(0.7)
                              : AppColors.muted,
                        ),
                      ),
                      onTap: () {
                        HapticFeedback.lightImpact();
                        languageProvider.setLanguage(code);
                        Navigator.pop(context);
                      },
                    ),
                  );
                }).toList(),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _VoiceAssistantView extends StatelessWidget {
  final double audioLevel;
  final Animation<double> fadeAnimation;

  const _VoiceAssistantView({
    required this.audioLevel,
    required this.fadeAnimation,
  });

  @override
  Widget build(BuildContext context) {
    final voiceProvider = context.watch<VoiceProvider>();
    final languageProvider = context.watch<LanguageProvider>();
    final connectionState = voiceProvider.connectionState;
    final isConnected = voiceProvider.isConnected;
    final isConnecting = connectionState == VoiceConnectionState.connecting;

    return FadeTransition(
      opacity: fadeAnimation,
      child: Container(
        decoration: BoxDecoration(
          gradient: isConnected
              ? LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    AppColors.primary.withOpacity(0.03),
                    AppColors.background,
                  ],
                )
              : null,
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Status indicator
              _buildStatusChip(connectionState, isConnected),

              // Voice visualization with SiriWaveOrb
              Expanded(
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SiriWaveOrb(
                        isActive: isConnected,
                        audioLevel: audioLevel,
                        size: 240,
                        onTap: isConnecting
                            ? null
                            : () async {
                                HapticFeedback.mediumImpact();
                                if (isConnected) {
                                  await voiceProvider.disconnect();
                                  if (context.mounted) {
                                    HapticFeedback.lightImpact();
                                  }
                                } else {
                                  await voiceProvider.connect(
                                    language: languageProvider.currentLanguageCode,
                                  );
                                  if (context.mounted && voiceProvider.isConnected) {
                                    HapticFeedback.heavyImpact();
                                  }
                                }
                              },
                      ),
                      const SizedBox(height: 40),
                      
                      // Status text
                      Text(
                        _getStatusText(connectionState, isConnected),
                        style: const TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.w700,
                          color: AppColors.ink,
                          letterSpacing: -0.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      
                      // Subtitle
                      Text(
                        _getSubtitleText(connectionState, isConnected),
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w400,
                          color: AppColors.muted,
                          height: 1.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),

              // Error message
              if (voiceProvider.errorMessage != null) ...[
                Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.errorLight,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.error.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: AppColors.error.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.error_outline_rounded,
                          color: AppColors.error,
                          size: 20,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          voiceProvider.errorMessage!,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: AppColors.error,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // Action buttons
              Column(
                children: [
                  if (!isConnected)
                    AnimatedOpacity(
                      opacity: isConnecting ? 0.5 : 1.0,
                      duration: const Duration(milliseconds: 200),
                      child: Container(
                        width: double.infinity,
                        height: 60,
                        decoration: BoxDecoration(
                          gradient: AppColors.greenGradient,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.green.withOpacity(0.3),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ElevatedButton.icon(
                          onPressed: isConnecting
                              ? null
                              : () async {
                                  HapticFeedback.mediumImpact();
                                  await voiceProvider.connect(
                                    language: languageProvider.currentLanguageCode,
                                  );
                                  if (context.mounted && voiceProvider.isConnected) {
                                    HapticFeedback.heavyImpact();
                                  }
                                },
                          icon: Icon(
                            isConnecting ? Icons.hourglass_empty_rounded : Icons.mic_rounded,
                            size: 24,
                          ),
                          label: Text(
                            isConnecting ? 'Connecting...' : 'Start Conversation',
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.transparent,
                            foregroundColor: Colors.white,
                            shadowColor: Colors.transparent,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                        ),
                      ),
                    )
                  else
                    Container(
                      width: double.infinity,
                      height: 60,
                      decoration: BoxDecoration(
                        color: AppColors.error,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.error.withOpacity(0.3),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: ElevatedButton.icon(
                        onPressed: () async {
                          HapticFeedback.mediumImpact();
                          await voiceProvider.disconnect();
                          if (context.mounted) {
                            HapticFeedback.lightImpact();
                          }
                        },
                        icon: const Icon(Icons.stop_rounded, size: 24),
                        label: const Text(
                          'End Conversation',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          foregroundColor: Colors.white,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                      ),
                    ),
                  const SizedBox(height: 16),
                  
                  // Info text
                  if (!isConnected)
                    const Text(
                      'Tap the button or orb to start a voice conversation',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w400,
                        color: AppColors.textTertiary,
                        height: 1.5,
                      ),
                    )
                  else
                    Text(
                      'Tap the orb or button to end • Session ${voiceProvider.sessionId?.substring(0, 8) ?? "active"}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        color: AppColors.textTertiary,
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusChip(VoiceConnectionState state, bool isConnected) {
    Color bgColor;
    Color textColor;
    IconData icon;
    String label;

    if (state == VoiceConnectionState.connecting) {
      bgColor = AppColors.warning.withOpacity(0.1);
      textColor = AppColors.warning;
      icon = Icons.sync_rounded;
      label = 'Connecting';
    } else if (state == VoiceConnectionState.error) {
      bgColor = AppColors.error.withOpacity(0.1);
      textColor = AppColors.error;
      icon = Icons.error_outline_rounded;
      label = 'Error';
    } else if (isConnected) {
      bgColor = AppColors.successLight;
      textColor = AppColors.success;
      icon = Icons.check_circle_rounded;
      label = 'Connected';
    } else {
      bgColor = AppColors.muted.withOpacity(0.1);
      textColor = AppColors.muted;
      icon = Icons.circle_outlined;
      label = 'Ready';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: textColor.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: textColor),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }

  String _getStatusText(VoiceConnectionState state, bool isConnected) {
    if (state == VoiceConnectionState.connecting) {
      return 'Connecting...';
    } else if (state == VoiceConnectionState.error) {
      return 'Connection Failed';
    } else if (isConnected) {
      return 'I\'m Listening';
    } else {
      return 'Ready to Help';
    }
  }

  String _getSubtitleText(VoiceConnectionState state, bool isConnected) {
    if (state == VoiceConnectionState.connecting) {
      return 'Setting up secure voice channel';
    } else if (state == VoiceConnectionState.error) {
      return 'Unable to connect to voice service';
    } else if (isConnected) {
      return 'Ask me anything about government services';
    } else {
      return 'Your AI assistant for government schemes and services';
    }
  }
}
