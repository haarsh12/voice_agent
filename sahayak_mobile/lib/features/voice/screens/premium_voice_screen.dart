import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/providers/language_provider.dart';
import '../../../shared/widgets/siri_wave_orb.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/voice_provider.dart';

/// Premium voice assistant screen with proper layout
/// 2/5 top: Voice circle
/// 3/5 bottom: Live transcript
class PremiumVoiceScreen extends StatefulWidget {
  const PremiumVoiceScreen({super.key});

  @override
  State<PremiumVoiceScreen> createState() => _PremiumVoiceScreenState();
}

class _PremiumVoiceScreenState extends State<PremiumVoiceScreen> {
  double _audioLevel = 0.0;
  Timer? _audioLevelTimer;
  final ScrollController _transcriptScroll = ScrollController();

  @override
  void dispose() {
    _audioLevelTimer?.cancel();
    _transcriptScroll.dispose();
    super.dispose();
  }

  void _startAudioLevelAnimation() {
    _audioLevelTimer?.cancel();
    int tick = 0;
    _audioLevelTimer = Timer.periodic(
      const Duration(milliseconds: 150),
      (timer) {
        if (!mounted) {
          timer.cancel();
          return;
        }
        tick++;
        final newLevel = 0.3 + (0.5 * ((tick % 10) / 10));
        setState(() => _audioLevel = newLevel);
      },
    );
  }

  void _stopAudioLevelAnimation() {
    _audioLevelTimer?.cancel();
    if (mounted) setState(() => _audioLevel = 0.0);
  }

  @override
  Widget build(BuildContext context) {
    final voiceProvider = context.watch<VoiceProvider>();
    final languageProvider = context.watch<LanguageProvider>();
    final authProvider = context.watch<AuthProvider>();
    final isGuest = !authProvider.isAuthenticated;

    // Manage audio animation
    if (voiceProvider.isConnected && _audioLevelTimer == null) {
      _startAudioLevelAnimation();
    } else if (!voiceProvider.isConnected && _audioLevelTimer != null) {
      _stopAudioLevelAnimation();
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA), // Light gray background
      body: SafeArea(
        child: Column(
          children: [
            // Header with user info
            _buildHeader(context, isGuest),

            // Voice Circle Section (2/5 of remaining space)
            Expanded(
              flex: 2,
              child: _buildVoiceSection(
                context,
                voiceProvider,
                languageProvider,
              ),
            ),

            // Live Transcript Section (3/5 of remaining space)
            Expanded(
              flex: 3,
              child: _buildTranscriptSection(context, voiceProvider),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, bool isGuest) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            offset: const Offset(0, 2),
            blurRadius: 8,
          ),
        ],
      ),
      child: Row(
        children: [
          // Logo/Title
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF06B6D4),
                  const Color(0xFF3B82F6),
                ],
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.support_agent_rounded,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          const Text(
            'Sahayak AI',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Color(0xFF1F2937),
              letterSpacing: -0.5,
            ),
          ),
          const Spacer(),
          
          // User icon or Guest mode indicator
          if (isGuest)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF3C7),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: const Color(0xFFF59E0B).withOpacity(0.3),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: Color(0xFFF59E0B),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  const Text(
                    'Guest',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFF59E0B),
                    ),
                  ),
                ],
              ),
            )
          else
            CircleAvatar(
              radius: 18,
              backgroundColor: const Color(0xFF10B981),
              child: const Icon(
                Icons.person,
                color: Colors.white,
                size: 20,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildVoiceSection(
    BuildContext context,
    VoiceProvider voiceProvider,
    LanguageProvider languageProvider,
  ) {
    final isConnected = voiceProvider.isConnected;
    final isConnecting = voiceProvider.connectionState == VoiceConnectionState.connecting;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: isConnected
              ? [
                  const Color(0xFFDCFCE7),
                  const Color(0xFFF8F9FA),
                ]
              : [
                  const Color(0xFFF8F9FA),
                  const Color(0xFFF8F9FA),
                ],
        ),
      ),
      child: Column(
        children: [
          const SizedBox(height: 16),

          // Horizontal scrolling language selector
          _buildLanguageSelector(languageProvider),

          const SizedBox(height: 24),

          // Voice Circle with SiriWaveOrb
          Expanded(
            child: Center(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Animated rings
                  if (isConnected) ...[
                    _buildPulsingRing(200, 0.3, const Color(0xFF10B981)),
                    _buildPulsingRing(240, 0.15, const Color(0xFF3B82F6)),
                  ],
                  
                  // Siri Wave Orb
                  SiriWaveOrb(
                    isActive: isConnected,
                    audioLevel: _audioLevel,
                    size: 160,
                    onTap: isConnecting
                        ? null
                        : () async {
                            HapticFeedback.mediumImpact();
                            if (isConnected) {
                              await voiceProvider.disconnect();
                              HapticFeedback.lightImpact();
                            } else {
                              await voiceProvider.connect(
                                language: languageProvider.currentLanguageCode,
                              );
                              if (voiceProvider.isConnected) {
                                HapticFeedback.heavyImpact();
                              }
                            }
                          },
                  ),
                ],
              ),
            ),
          ),

          // Action buttons
          _buildActionButtons(context, voiceProvider, languageProvider, isConnecting),

          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildLanguageSelector(LanguageProvider languageProvider) {
    return SizedBox(
      height: 90,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: LanguageProvider.supportedLocales.length,
        itemBuilder: (context, index) {
          final locale = LanguageProvider.supportedLocales[index];
          final code = locale.languageCode;
          final isSelected = languageProvider.currentLanguageCode == code;

          return GestureDetector(
            onTap: () {
              HapticFeedback.lightImpact();
              languageProvider.setLanguage(code);
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 80,
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              decoration: BoxDecoration(
                gradient: isSelected
                    ? LinearGradient(
                        colors: [
                          const Color(0xFF10B981),
                          const Color(0xFF059669),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      )
                    : null,
                color: isSelected ? null : Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isSelected
                      ? const Color(0xFF10B981)
                      : const Color(0xFFE5E7EB),
                  width: isSelected ? 2 : 1,
                ),
                boxShadow: [
                  BoxShadow(
                    color: isSelected
                        ? const Color(0xFF10B981).withOpacity(0.3)
                        : Colors.black.withOpacity(0.05),
                    offset: const Offset(0, 4),
                    blurRadius: isSelected ? 12 : 8,
                  ),
                ],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    LanguageProvider.languageScriptNames[code] ?? '',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: isSelected ? Colors.white : const Color(0xFF1F2937),
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 1,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    LanguageProvider.languageNames[code] ?? '',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: isSelected
                          ? Colors.white.withOpacity(0.9)
                          : const Color(0xFF6B7280),
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildPulsingRing(double size, double opacity, Color color) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 1500),
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: color.withOpacity(opacity),
          width: 2,
        ),
      ),
    );
  }

  Widget _buildActionButtons(
    BuildContext context,
    VoiceProvider voiceProvider,
    LanguageProvider languageProvider,
    bool isConnecting,
  ) {
    final isConnected = voiceProvider.isConnected;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          // New Session button
          _buildIconButton(
            icon: Icons.fiber_new_rounded,
            label: 'New',
            color: const Color(0xFF8B5CF6),
            onTap: () async {
              HapticFeedback.mediumImpact();
              if (isConnected) {
                await voiceProvider.disconnect();
              }
              // Start new session
              await voiceProvider.connect(
                language: languageProvider.currentLanguageCode,
              );
            },
          ),

          const SizedBox(width: 12),

          // Main connect/disconnect button
          Expanded(
            child: GestureDetector(
              onTap: isConnecting
                  ? null
                  : () async {
                      HapticFeedback.mediumImpact();
                      if (isConnected) {
                        await voiceProvider.disconnect();
                        HapticFeedback.lightImpact();
                      } else {
                        await voiceProvider.connect(
                          language: languageProvider.currentLanguageCode,
                        );
                        if (voiceProvider.isConnected) {
                          HapticFeedback.heavyImpact();
                        }
                      }
                    },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                height: 56,
                decoration: BoxDecoration(
                  gradient: isConnected
                      ? LinearGradient(
                          colors: [
                            const Color(0xFFEF4444),
                            const Color(0xFFDC2626),
                          ],
                        )
                      : LinearGradient(
                          colors: [
                            const Color(0xFF10B981),
                            const Color(0xFF059669),
                          ],
                        ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: (isConnected
                              ? const Color(0xFFEF4444)
                              : const Color(0xFF10B981))
                          .withOpacity(0.4),
                      offset: const Offset(0, 4),
                      blurRadius: 16,
                    ),
                  ],
                ),
                child: Center(
                  child: isConnecting
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              isConnected
                                  ? Icons.stop_rounded
                                  : Icons.mic_rounded,
                              color: Colors.white,
                              size: 24,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              isConnected ? 'End Session' : 'Start Speaking',
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                                letterSpacing: 0.3,
                              ),
                            ),
                          ],
                        ),
                ),
              ),
            ),
          ),

          const SizedBox(width: 12),

          // Upload document button
          _buildIconButton(
            icon: Icons.upload_file_rounded,
            label: 'Upload',
            color: const Color(0xFF3B82F6),
            onTap: () {
              HapticFeedback.lightImpact();
              // TODO: Implement document upload
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Document upload coming soon'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildIconButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 72,
        height: 56,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 2,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              offset: const Offset(0, 2),
              blurRadius: 8,
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTranscriptSection(
      BuildContext context, VoiceProvider voiceProvider) {
    final transcript = voiceProvider.transcript;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            offset: const Offset(0, -4),
            blurRadius: 16,
          ),
        ],
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(
                  color: const Color(0xFFE5E7EB),
                  width: 1,
                ),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        const Color(0xFF8B5CF6),
                        const Color(0xFF7C3AED),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(
                    Icons.chat_bubble_rounded,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                const Text(
                  'Live Transcript',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF1F2937),
                  ),
                ),
                const Spacer(),
                if (voiceProvider.isConnected)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(
                            color: Color(0xFF10B981),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        const Text(
                          'LIVE',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF10B981),
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),

          // Transcript list
          Expanded(
            child: transcript.isEmpty
                ? Center(
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
                  )
                : ListView.builder(
                    controller: _transcriptScroll,
                    reverse: true, // Scroll upwards like chat
                    padding: const EdgeInsets.all(20),
                    itemCount: transcript.length,
                    itemBuilder: (context, index) {
                      final reversedIndex = transcript.length - 1 - index;
                      final entry = transcript[reversedIndex];
                      final isUser = entry['role'] == 'user';

                      return Align(
                        alignment: isUser
                            ? Alignment.centerRight
                            : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.75,
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
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: isUser
                                ? [
                                    BoxShadow(
                                      color: const Color(0xFF3B82F6)
                                          .withOpacity(0.3),
                                      offset: const Offset(0, 2),
                                      blurRadius: 8,
                                    ),
                                  ]
                                : null,
                          ),
                          child: Text(
                            entry['text'] ?? '',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w500,
                              color: isUser
                                  ? Colors.white
                                  : const Color(0xFF1F2937),
                              height: 1.4,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
