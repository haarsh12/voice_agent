import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/providers/language_provider.dart';
import '../../../shared/widgets/siri_wave_orb.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/voice_provider.dart';

/// Premium voice assistant screen with live transcript
class PremiumVoiceScreenV2 extends StatefulWidget {
  const PremiumVoiceScreenV2({super.key});

  @override
  State<PremiumVoiceScreenV2> createState() => _PremiumVoiceScreenV2State();
}

class _PremiumVoiceScreenV2State extends State<PremiumVoiceScreenV2> {
  double _audioLevel = 0.0;
  Timer? _audioLevelTimer;
  final ScrollController _transcriptScroll = ScrollController();
  final TextEditingController _messageController = TextEditingController();
  final FocusNode _messageFocusNode = FocusNode();
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final voiceProvider = context.read<VoiceProvider>();
      voiceProvider.addListener(_onVoiceUpdate);
    });
  }

  @override
  void dispose() {
    try {
      final voiceProvider = context.read<VoiceProvider>();
      voiceProvider.removeListener(_onVoiceUpdate);
    } catch (_) {}
    _audioLevelTimer?.cancel();
    _transcriptScroll.dispose();
    _messageController.dispose();
    _messageFocusNode.dispose();
    super.dispose();
  }

  void _onVoiceUpdate() {
    if (mounted) {
      setState(() {});
      // Auto scroll transcript to bottom
      if (_transcriptScroll.hasClients) {
        Future.delayed(const Duration(milliseconds: 100), () {
          if (_transcriptScroll.hasClients && mounted) {
            _transcriptScroll.animateTo(
              _transcriptScroll.position.maxScrollExtent,
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut,
            );
          }
        });
      }
    }
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
        if (mounted) {
          setState(() => _audioLevel = newLevel);
        }
      },
    );
  }

  void _stopAudioLevelAnimation() {
    _audioLevelTimer?.cancel();
    if (mounted) setState(() => _audioLevel = 0.0);
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );

      if (image != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Selected: ${image.name}'),
            backgroundColor: const Color(0xFF10B981),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to pick image: $e'),
            backgroundColor: const Color(0xFFEF4444),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Future<void> _pickDocument() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx', 'txt'],
      );

      if (result != null && mounted) {
        final file = result.files.first;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Selected: ${file.name}'),
            backgroundColor: const Color(0xFF10B981),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to pick document: $e'),
            backgroundColor: const Color(0xFFEF4444),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFFE5E7EB),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Choose Image Source',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF1F2937),
                ),
              ),
              const SizedBox(height: 20),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.camera_alt_rounded,
                    color: Colors.black,
                  ),
                ),
                title: const Text(
                  'Camera',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.photo_library_rounded,
                    color: Colors.black,
                  ),
                ),
                title: const Text(
                  'Gallery',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.gallery);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    final voiceProvider = context.read<VoiceProvider>();
    
    // Send text - VoiceProvider handles it whether connected or not
    voiceProvider.sendText(text);

    _messageController.clear();
    HapticFeedback.lightImpact();
    
    // Trigger UI update
    setState(() {});
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
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            _buildHeader(context, isGuest),

            // Language Pills
            _buildLanguageSelector(languageProvider),

            const SizedBox(height: 16),

            // Voice Circle (smaller now)
            _buildVoiceCircle(context, voiceProvider, languageProvider),

            const SizedBox(height: 12),

            // "Tap to start" text
            Text(
              voiceProvider.isConnected ? 'Listening...' : 'Tap to start',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Color(0xFF374151),
                letterSpacing: -0.2,
              ),
            ),
            const SizedBox(height: 4),

            // Subtitle
            const Text(
              'Live transcript will appear below',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w400,
                color: Color(0xFF9CA3AF),
              ),
            ),

            const SizedBox(height: 16),

            // Divider
            Container(
              height: 1,
              color: const Color(0xFFE5E7EB),
              margin: const EdgeInsets.symmetric(horizontal: 20),
            ),

            // Live Transcript Section (replaces greeting)
            Expanded(
              child: _buildLiveTranscript(context, voiceProvider),
            ),

            // Input row
            _buildInputRow(context),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, bool isGuest) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: const BoxDecoration(
              color: Color(0xFFF3F4F6),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.person_outline_rounded,
              color: Color(0xFF6B7280),
              size: 20,
            ),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'Guest',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF111827),
                ),
              ),
              Text(
                'Sahayak AI',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w400,
                  color: Color(0xFF6B7280),
                ),
              ),
            ],
          ),
          const Spacer(),
          GestureDetector(
            onTap: () {
              context.push('/login');
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 7),
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFFE5E7EB), width: 1.5),
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Text(
                'Sign in',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF111827),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageSelector(LanguageProvider languageProvider) {
    return SizedBox(
      height: 38,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: LanguageProvider.supportedLocales.length,
        itemBuilder: (context, index) {
          final locale = LanguageProvider.supportedLocales[index];
          final code = locale.languageCode;
          final isSelected = languageProvider.currentLanguageCode == code;
          final displayName = LanguageProvider.languageNames[code] ?? '';

          return Padding(
            padding: const EdgeInsets.only(right: 10),
            child: GestureDetector(
              onTap: () {
                HapticFeedback.lightImpact();
                languageProvider.setLanguage(code);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
                decoration: BoxDecoration(
                  color: isSelected ? Colors.black : Colors.white,
                  borderRadius: BorderRadius.circular(19),
                  border: Border.all(
                    color: isSelected ? Colors.black : const Color(0xFFE5E7EB),
                    width: 1.5,
                  ),
                ),
                child: Center(
                  child: Text(
                    displayName,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isSelected ? Colors.white : const Color(0xFF111827),
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildVoiceCircle(
    BuildContext context,
    VoiceProvider voiceProvider,
    LanguageProvider languageProvider,
  ) {
    final isConnected = voiceProvider.isConnected;
    final isConnecting =
        voiceProvider.connectionState == VoiceConnectionState.connecting;

    return GestureDetector(
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
      child: Container(
        width: 140,
        height: 140,
        decoration: const BoxDecoration(
          color: Color(0xFFF3F4F6),
          shape: BoxShape.circle,
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            if (isConnected)
              SiriWaveOrb(
                isActive: true,
                audioLevel: _audioLevel,
                size: 140,
                idleColor: const Color(0xFF6B7280),
              )
            else
              const Icon(
                Icons.mic_rounded,
                size: 48,
                color: Color(0xFF6B7280),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildLiveTranscript(BuildContext context, VoiceProvider voiceProvider) {
    final transcript = voiceProvider.transcript;
    final hasTranscript = transcript.isNotEmpty;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: hasTranscript ? Colors.white : const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFFE5E7EB),
          width: 1.5,
        ),
      ),
      child: hasTranscript
          ? ListView.builder(
              controller: _transcriptScroll,
              padding: const EdgeInsets.all(20),
              itemCount: transcript.length,
              itemBuilder: (context, index) {
                final entry = transcript[index];
                final speaker = entry['speaker']?.toString() ?? 'user';
                final isUser = speaker == 'user';
                final text = entry['text']?.toString() ?? '';

                return Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isUser 
                        ? const Color(0xFFF3F4F6) 
                        : const Color(0xFFECFDF5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Label: YOU or SAHAYAK AI
                      Text(
                        isUser ? 'YOU' : 'SAHAYAK AI',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: const Color(0xFF6B7280),
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // Message text
                      Text(
                        text,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w400,
                          color: Color(0xFF111827),
                          height: 1.6,
                        ),
                      ),
                    ],
                  ),
                );
              },
            )
          : Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Text(
                      'Good morning, there! 👋',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF111827),
                        letterSpacing: -0.5,
                      ),
                    ),
                    SizedBox(height: 10),
                    Text(
                      'Ask me anything about government\nschemes, grievances, or services.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w400,
                        color: Color(0xFF6B7280),
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildInputRow(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(
            color: Color(0xFFE5E7EB),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          // Camera icon
          GestureDetector(
            onTap: () {
              HapticFeedback.lightImpact();
              _showImageSourceDialog();
            },
            child: Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFFE5E7EB),
                  width: 1.5,
                ),
              ),
              child: const Icon(
                Icons.camera_alt_rounded,
                color: Color(0xFF6B7280),
                size: 19,
              ),
            ),
          ),
          const SizedBox(width: 8),

          // Upload/File icon
          GestureDetector(
            onTap: () {
              HapticFeedback.lightImpact();
              _pickDocument();
            },
            child: Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                border: Border.all(
                  color: const Color(0xFFE5E7EB),
                  width: 1.5,
                ),
              ),
              child: const Icon(
                Icons.upload_file_rounded,
                color: Color(0xFF6B7280),
                size: 19,
              ),
            ),
          ),
          const SizedBox(width: 10),

          // Text field - properly rounded with black border
          Expanded(
            child: Container(
              height: 38,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(19),
                border: Border.all(
                  color: Colors.black,
                  width: 1.5,
                ),
              ),
              child: TextField(
                controller: _messageController,
                focusNode: _messageFocusNode,
                decoration: const InputDecoration(
                  hintText: 'Type a message...',
                  hintStyle: TextStyle(
                    color: Color(0xFF9CA3AF),
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                  ),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  isDense: true,
                ),
                style: const TextStyle(
                  fontSize: 14,
                  color: Color(0xFF111827),
                ),
                maxLines: 1,
                textInputAction: TextInputAction.send,
                onChanged: (_) => setState(() {}),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
          ),
          const SizedBox(width: 8),

          // Send button - only shows when text entered
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: _messageController.text.trim().isEmpty ? 0 : 38,
            height: 38,
            child: _messageController.text.trim().isEmpty
                ? const SizedBox.shrink()
                : GestureDetector(
                    onTap: _sendMessage,
                    child: Container(
                      decoration: const BoxDecoration(
                        color: Colors.black,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.send_rounded,
                        color: Colors.white,
                        size: 18,
                      ),
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
