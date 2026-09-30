@echo off
REM Sahayak AI Mobile - Quick Run Script

echo ===============================================
echo    Sahayak AI - Mobile Application Runner
echo ===============================================
echo.

REM Check if Flutter is installed
flutter --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Flutter is not installed or not in PATH
    echo Please install Flutter from https://flutter.dev
    pause
    exit /b 1
)

echo Flutter version:
flutter --version
echo.

REM Check for connected devices
echo Checking for connected devices...
flutter devices
echo.

echo Choose an option:
echo 1. Run in Debug mode (default)
echo 2. Run in Release mode
echo 3. Run with custom backend URL
echo 4. Clean and rebuild
echo 5. Build APK
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Running in DEBUG mode...
    flutter run
) else if "%choice%"=="2" (
    echo.
    echo Running in RELEASE mode...
    flutter run --release
) else if "%choice%"=="3" (
    echo.
    set /p backend_url="Enter backend URL (e.g., http://192.168.1.100:8000): "
    echo Running with backend URL: %backend_url%
    flutter run --dart-define=API_BASE_URL=%backend_url%
) else if "%choice%"=="4" (
    echo.
    echo Cleaning and rebuilding...
    flutter clean
    flutter pub get
    flutter run
) else if "%choice%"=="5" (
    echo.
    echo Building APK...
    flutter build apk --release
    echo.
    echo APK built successfully!
    echo Location: build\app\outputs\flutter-apk\app-release.apk
    pause
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

pause
