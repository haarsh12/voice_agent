import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_colors.dart';
import '../providers/voice_provider.dart';

/// Voice waveform visualization
class VoiceWaveform extends StatefulWidget {
  const VoiceWaveform({super.key});

  @override
  State<VoiceWaveform> createState() => _VoiceWaveformState();
}

class _VoiceWaveformState extends State<VoiceWaveform>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final voiceProvider = context.watch<VoiceProvider>();
    final isConnected = voiceProvider.isConnected;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isConnected
                ? AppColors.primary.withOpacity(0.1)
                : AppColors.surfaceVariant,
            boxShadow: isConnected
                ? [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.2),
                      blurRadius: 30,
                      spreadRadius: 10,
                    ),
                  ]
                : null,
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Animated rings when connected
              if (isConnected) ...[
                _buildAnimatedRing(0.7, _controller.value),
                _buildAnimatedRing(0.85, (_controller.value + 0.3) % 1.0),
                _buildAnimatedRing(1.0, (_controller.value + 0.6) % 1.0),
              ],
              
              // Center icon
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isConnected ? AppColors.primary : AppColors.voiceInactive,
                ),
                child: Icon(
                  isConnected ? Icons.mic : Icons.mic_off,
                  size: 56,
                  color: Colors.white,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAnimatedRing(double baseScale, double animationValue) {
    final scale = baseScale + (animationValue * 0.3);
    final opacity = (1.0 - animationValue) * 0.5;

    return Transform.scale(
      scale: scale,
      child: Container(
        width: 200,
        height: 200,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: AppColors.primary.withOpacity(opacity),
            width: 2,
          ),
        ),
      ),
    );
  }
}
