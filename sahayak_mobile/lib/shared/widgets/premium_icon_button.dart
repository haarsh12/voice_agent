import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/theme/app_colors.dart';

enum IconButtonStyle {
  filled,
  outlined,
  ghost,
}

/// Modern icon button with smooth animations and proper shadows
class PremiumIconButton extends StatefulWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final IconButtonStyle style;
  final Color? backgroundColor;
  final Color? iconColor;
  final double size;
  final String? tooltip;
  final bool showBadge;
  final String? badgeText;

  const PremiumIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.style = IconButtonStyle.filled,
    this.backgroundColor,
    this.iconColor,
    this.size = 48.0,
    this.tooltip,
    this.showBadge = false,
    this.badgeText,
  });

  @override
  State<PremiumIconButton> createState() => _PremiumIconButtonState();
}

class _PremiumIconButtonState extends State<PremiumIconButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  bool _isPressed = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 150),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.92).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    if (widget.onPressed != null) {
      setState(() => _isPressed = true);
      _controller.forward();
      HapticFeedback.lightImpact();
    }
  }

  void _handleTapUp(TapUpDetails details) {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  void _handleTapCancel() {
    setState(() => _isPressed = false);
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final button = ScaleTransition(
      scale: _scaleAnimation,
      child: GestureDetector(
        onTapDown: _handleTapDown,
        onTapUp: _handleTapUp,
        onTapCancel: _handleTapCancel,
        onTap: widget.onPressed,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: widget.size,
          height: widget.size,
          decoration: BoxDecoration(
            color: _getBackgroundColor(),
            shape: BoxShape.circle,
            border: _getBorder(),
            boxShadow: _getShadow(),
          ),
          child: Center(
            child: Icon(
              widget.icon,
              size: widget.size * 0.45,
              color: _getIconColor(),
            ),
          ),
        ),
      ),
    );

    if (widget.showBadge) {
      return Stack(
        clipBehavior: Clip.none,
        children: [
          button,
          Positioned(
            right: 0,
            top: 0,
            child: Container(
              padding: EdgeInsets.all(widget.badgeText != null ? 4 : 6),
              decoration: BoxDecoration(
                color: AppColors.error,
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.surface, width: 2),
              ),
              child: widget.badgeText != null
                  ? Text(
                      widget.badgeText!,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                      ),
                    )
                  : const SizedBox(),
            ),
          ),
        ],
      );
    }

    if (widget.tooltip != null) {
      return Tooltip(
        message: widget.tooltip!,
        child: button,
      );
    }

    return button;
  }

  Color _getBackgroundColor() {
    final isDisabled = widget.onPressed == null;
    
    if (isDisabled) {
      return AppColors.muted.withOpacity(0.2);
    }

    if (widget.backgroundColor != null) {
      return widget.backgroundColor!;
    }

    switch (widget.style) {
      case IconButtonStyle.filled:
        return _isPressed ? AppColors.surfaceVariant : AppColors.surface;
      case IconButtonStyle.outlined:
        return _isPressed ? AppColors.hoverBackground : Colors.transparent;
      case IconButtonStyle.ghost:
        return _isPressed ? AppColors.hoverBackground : Colors.transparent;
    }
  }

  Color _getIconColor() {
    final isDisabled = widget.onPressed == null;
    
    if (isDisabled) {
      return AppColors.muted;
    }

    if (widget.iconColor != null) {
      return widget.iconColor!;
    }

    return AppColors.textPrimary;
  }

  Border? _getBorder() {
    if (widget.style == IconButtonStyle.outlined) {
      return Border.all(
        color: _isPressed ? AppColors.strongLine : AppColors.border,
        width: 1.5,
      );
    }
    return null;
  }

  List<BoxShadow>? _getShadow() {
    final isDisabled = widget.onPressed == null;
    
    if (isDisabled || _isPressed || widget.style == IconButtonStyle.ghost) {
      return null;
    }

    return AppColors.cardShadow;
  }
}
