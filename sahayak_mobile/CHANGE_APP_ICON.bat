@echo off
REM Quick script to change app icon

echo ========================================
echo   Sahayak AI - Change App Icon
echo ========================================
echo.

REM Check if logo exists
if not exist "assets\logo\app_icon.png" (
    echo [ERROR] Logo file not found!
    echo.
    echo Please place your logo as:
    echo   assets\logo\app_icon.png
    echo.
    echo Logo requirements:
    echo   - PNG format
    echo   - 1024x1024 pixels recommended
    echo   - Transparent background or solid color
    echo.
    pause
    exit /b 1
)

echo [OK] Logo file found: assets\logo\app_icon.png
echo.

echo Step 1: Installing flutter_launcher_icons...
call flutter pub get
echo.

echo Step 2: Generating app icons...
call flutter pub run flutter_launcher_icons
echo.

echo Step 3: Cleaning build...
call flutter clean
echo.

echo ========================================
echo   App Icon Changed Successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Build app: flutter build apk
echo 2. Install on device to see new icon
echo.

pause
