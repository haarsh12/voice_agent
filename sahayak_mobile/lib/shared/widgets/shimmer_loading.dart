import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

/// Shimmer loading effect for skeleton screens
/// Provides premium loading feedback while content loads
class ShimmerLoading extends StatefulWidget {
  final Widget child;
  final bool isLoading;
  final Color? baseColor;
  final Color? highlightColor;

  const ShimmerLoading({
    super.key,
    required this.child,
    this.isLoading = true,
    this.baseColor,
    this.highlightColor,
  });

  @override
  State<ShimmerLoading> createState() => _ShimmerLoadingState();
}

class _ShimmerLoadingState extends State<ShimmerLoading>
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
    if (!widget.isLoading) {
      return widget.child;
    }

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return ShaderMask(
          shaderCallback: (bounds) {
            return LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              stops: [
                _controller.value - 0.3,
                _controller.value,
                _controller.value + 0.3,
              ].map((e) => e.clamp(0.0, 1.0)).toList(),
              colors: [
                widget.baseColor ?? AppColors.surfaceVariant,
                widget.highlightColor ?? AppColors.hoverBackground,
                widget.baseColor ?? AppColors.surfaceVariant,
              ],
            ).createShader(bounds);
          },
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

/// Shimmer skeleton for card loading
class ShimmerCard extends StatelessWidget {
  final double? height;
  final double? width;
  final BorderRadius? borderRadius;

  const ShimmerCard({
    super.key,
    this.height,
    this.width,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    return ShimmerLoading(
      child: Container(
        height: height,
        width: width,
        decoration: BoxDecoration(
          color: AppColors.surfaceVariant,
          borderRadius: borderRadius ?? BorderRadius.circular(12),
        ),
      ),
    );
  }
}

/// Shimmer skeleton for text lines
class ShimmerText extends StatelessWidget {
  final double width;
  final double height;

  const ShimmerText({
    super.key,
    this.width = 100,
    this.height = 14,
  });

  @override
  Widget build(BuildContext context) {
    return ShimmerLoading(
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: AppColors.surfaceVariant,
          borderRadius: BorderRadius.circular(4),
        ),
      ),
    );
  }
}

/// Shimmer skeleton for circular avatars/icons
class ShimmerCircle extends StatelessWidget {
  final double size;

  const ShimmerCircle({
    super.key,
    this.size = 48,
  });

  @override
  Widget build(BuildContext context) {
    return ShimmerLoading(
      child: Container(
        width: size,
        height: size,
        decoration: const BoxDecoration(
          color: AppColors.surfaceVariant,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}

/// Complete scheme card skeleton
class ShimmerSchemeCard extends StatelessWidget {
  const ShimmerSchemeCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const ShimmerCircle(size: 40),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ShimmerText(
                      width: MediaQuery.of(context).size.width * 0.5,
                      height: 16,
                    ),
                    const SizedBox(height: 8),
                    const ShimmerText(width: 80, height: 12),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const ShimmerText(width: double.infinity, height: 14),
          const SizedBox(height: 6),
          const ShimmerText(width: double.infinity, height: 14),
          const SizedBox(height: 6),
          ShimmerText(
            width: MediaQuery.of(context).size.width * 0.6,
            height: 14,
          ),
        ],
      ),
    );
  }
}

/// Complete service card skeleton
class ShimmerServiceCard extends StatelessWidget {
  const ShimmerServiceCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const ShimmerCircle(size: 56),
          const SizedBox(height: 12),
          ShimmerText(
            width: MediaQuery.of(context).size.width * 0.25,
            height: 14,
          ),
          const SizedBox(height: 6),
          ShimmerText(
            width: MediaQuery.of(context).size.width * 0.15,
            height: 12,
          ),
        ],
      ),
    );
  }
}

/// Knowledge item skeleton
class ShimmerKnowledgeItem extends StatelessWidget {
  const ShimmerKnowledgeItem({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          const ShimmerCircle(size: 40),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ShimmerText(
                  width: MediaQuery.of(context).size.width * 0.6,
                  height: 16,
                ),
                const SizedBox(height: 8),
                const ShimmerText(width: 100, height: 12),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// List skeleton with multiple items
class ShimmerList extends StatelessWidget {
  final int itemCount;
  final Widget itemBuilder;

  const ShimmerList({
    super.key,
    this.itemCount = 5,
    required this.itemBuilder,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: itemCount,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) => itemBuilder,
    );
  }
}

/// Grid skeleton with multiple items
class ShimmerGrid extends StatelessWidget {
  final int itemCount;
  final Widget itemBuilder;
  final int crossAxisCount;

  const ShimmerGrid({
    super.key,
    this.itemCount = 6,
    required this.itemBuilder,
    this.crossAxisCount = 2,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 1.1,
      ),
      itemCount: itemCount,
      itemBuilder: (context, index) => itemBuilder,
    );
  }
}
