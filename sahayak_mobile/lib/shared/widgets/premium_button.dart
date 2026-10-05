import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/theme/app_colors.dart';

enum PremiumButtonStyle {
  primary,
  secondary,
  outline,
  ghost,
  success,
  danger,
}

enum PremiumButtonSize {
  small,
  medium,
  large,
}

/// Premium button with modern design - fully rounded, smooth animations, proper shadows
class PremiumButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final PremiumButtonStyle style;
  final PremiumButtonSize size;
  final IconData? icon;
  final bool isLoading;
  final bool isFullWidth;
  final double? width;
  final Widget? child;

  const PremiumButton({
    super.key,
    this.text = '',
    required this.onPressed,
    this.style = PremiumButtonStyle.primary,
    this.size = PremiumButtonSize.medium,
    this.icon,
    this.isLoading = false,
    this.isFullWidth = false,
    this.width,
    this.child,
  });

  @override
  State<PremiumButton> createState() => _PremiumButtonState();
}

class _PremiumButtonState extends State<PremiumButton>
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
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.96).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    if (widget.onPressed != null && !widget.isLoading) {
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
    final buttonSizes = {
      PremiumButtonSize.small: (height: 40.0, padding: 16.0, fontSize: 14.0, iconSize: 16.0),
      PremiumButtonSize.medium: (height: 48.0, padding: 20.0, fontSize: 15.0, iconSize: 18.0),
      PremiumButtonSize.large: (height: 56.0, padding: 24.0, fontSize: 16.0, iconSize: 20.0),
    };

    final size = buttonSizes[widget.size]!;
    final isDisabled = widget.onPressed == null || widget.isLoading;

    return ScaleTransition(
      scale: _scaleAnimation,
      child: GestureDetector(
        onTapDown: _handleTapDown,
        onTapUp: _handleTapUp,
        onTapCancel: _handleTapCancel,
        onTap: isDisabled ? null : widget.onPressed,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeInOut,
          width: widget.isFullWidth ? double.infinity : widget.width,
          height: size.height,
          decoration: BoxDecoration(
            gradient: _getGradient(),
            color: _getBackgroundColor(),
            borderRadius: BorderRadius.circular(size.height / 2), // Fully rounded
            border: _getBorder(),
            boxShadow: _getShadow(),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: isDisabled ? null : widget.onPressed,
              borderRadius: BorderRadius.circular(size.height / 2),
              splashColor: _getSplashColor(),
              highlightColor: Colors.transparent,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: size.padding),
                child: Row(
                  mainAxisSize: widget.isFullWidth ? MainAxisSize.max : MainAxisSize.min,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (widget.isLoading)
                      SizedBox(
                        width: size.iconSize,
                        height: size.iconSize,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(_getTextColor()),
                        ),
                      )
                    else if (widget.icon != null) ...[
                      Icon(
                        widget.icon,
                        size: size.iconSize,
                        color: _getTextColor(),
                      ),
                      if (widget.text.isNotEmpty || widget.child != null) const SizedBox(width: 8),
                    ],
                    if (widget.child != null)
                      widget.child!
                    else if (widget.text.isNotEmpty)
                      Text(
                        widget.text,
                        style: TextStyle(
                          fontSize: size.fontSize,
                          fontWeight: FontWeight.w600,
                          color: _getTextColor(),
                          letterSpacing: 0.3,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  LinearGradient? _getGradient() {
    if (widget.style == PremiumButtonStyle.primary && !_isPressed) {
      return AppColors.primaryGradient;
    }
    if (widget.style == PremiumButtonStyle.success && !_isPressed) {
      return AppColors.greenGradient;
    }
    return null;
  }

  Color _getBackgroundColor() {
    final isDisabled = widget.onPressed == null || widget.isLoading;
    
    if (isDisabled) {
      return AppColors.muted.withOpacity(0.3);
    }

    switch (widget.style) {
      case PremiumButtonStyle.primary:
        return _isPressed ? AppColors.primaryDark : AppColors.primary;
      case PremiumButtonStyle.secondary:
        return _isPressed ? AppColors.surfaceVariant : AppColors.chipBackground;
      case PremiumButtonStyle.outline:
        return _isPressed ? AppColors.hoverBackground : Colors.transparent;
      case PremiumButtonStyle.ghost:
        return _isPressed ? AppColors.hoverBackground : Colors.transparent;
      case PremiumButtonStyle.success:
        return _isPressed ? AppColors.greenDark : AppColors.green;
      case PremiumButtonStyle.danger:
        return _isPressed ? const Color(0xFFDC2626) : AppColors.error;
    }
  }

  Color _getTextColor() {
    final isDisabled = widget.onPressed == null || widget.isLoading;
    
    if (isDisabled) {
      return AppColors.muted;
    }

    switch (widget.style) {
      case PremiumButtonStyle.primary:
      case PremiumButtonStyle.success:
      case PremiumButtonStyle.danger:
        return Colors.white;
      case PremiumButtonStyle.secondary:
        return AppColors.textPrimary;
      case PremiumButtonStyle.outline:
      case PremiumButtonStyle.ghost:
        return AppColors.textPrimary;
    }
  }

  Border? _getBorder() {
    if (widget.style == PremiumButtonStyle.outline) {
      return Border.all(
        color: _isPressed ? AppColors.strongLine : AppColors.border,
        width: 1.5,
      );
    }
    return null;
  }

  List<BoxShadow>? _getShadow() {
    final isDisabled = widget.onPressed == null || widget.isLoading;
    
    if (isDisabled || _isPressed) {
      return null;
    }

    switch (widget.style) {
      case PremiumButtonStyle.primary:
        return [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.3),
            offset: const Offset(0, 4),
            blurRadius: 12,
            spreadRadius: 0,
          ),
        ];
      case PremiumButtonStyle.success:
        return [
          BoxShadow(
            color: AppColors.green.withOpacity(0.3),
            offset: const Offset(0, 4),
            blurRadius: 12,
            spreadRadius: 0,
          ),
        ];
      case PremiumButtonStyle.danger:
        return [
          BoxShadow(
            color: AppColors.error.withOpacity(0.3),
            offset: const Offset(0, 4),
            blurRadius: 12,
            spreadRadius: 0,
          ),
        ];
      case PremiumButtonStyle.secondary:
        return AppColors.cardShadow;
      default:
        return null;
    }
  }

  Color _getSplashColor() {
    switch (widget.style) {
      case PremiumButtonStyle.primary:
        return Colors.white.withOpacity(0.2);
      case PremiumButtonStyle.success:
        return Colors.white.withOpacity(0.2);
      case PremiumButtonStyle.danger:
        return Colors.white.withOpacity(0.2);
      default:
        return AppColors.ripple;
    }
  }
}
