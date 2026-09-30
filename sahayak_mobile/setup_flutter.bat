@echo off
REM Setup script for Sahayak Mobile Flutter App

echo ========================================
echo Sahayak Mobile - Flutter Setup
echo ========================================
echo.

echo Checking Flutter installation...
flutter --version
if %errorlevel% neq 0 (
    echo ERROR: Flutter is not installed or not in PATH
    echo Please install Flutter from https://docs.flutter.dev/get-started/install/windows
    pause
    exit /b 1
)
echo.

echo Running Flutter Doctor...
flutter doctor
echo.

echo Installing dependencies...
flutter pub get
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Connect your Android device or start an emulator
echo 2. Run: flutter devices (to check connected devices)
echo 3. Run: flutter run (to start the app)
echo.
echo For development:
echo - Press 'r' for hot reload
echo - Press 'R' for hot restart
echo - Press 'q' to quit
echo.
pause
