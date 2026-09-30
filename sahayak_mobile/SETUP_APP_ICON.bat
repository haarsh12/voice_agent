@echo off
echo ========================================
echo Sahayak AI - App Icon Setup
echo ========================================
echo.
echo INSTRUCTIONS:
echo 1. Save your app icon (red circular chat bubble logo) as:
echo    sahayak_mobile\assets\logo\app_icon.png
echo    - Size: 1024x1024 pixels (recommended)
echo    - Format: PNG with transparent or solid background
echo.
echo 2. For adaptive icon (Android), optionally create:
echo    sahayak_mobile\assets\logo\app_icon_fg.png
echo    - This is the foreground layer (your logo)
echo    - Background color is set to #A73439 (red) in pubspec.yaml
echo.
echo 3. After placing the icon files, press any key to generate icons...
pause
echo.
echo Generating app icons...
cd /d "%~dp0"
flutter pub run flutter_launcher_icons
echo.
echo ========================================
echo Icon generation complete!
echo ========================================
echo.
echo Next steps:
echo 1. Rebuild the app: flutter build apk --release
echo 2. Or run: flutter run
echo.
pause
