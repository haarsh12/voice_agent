@echo off
REM Quick launcher for Sahayak AI Mobile App

title Sahayak AI - Mobile App Launcher

echo ========================================
echo   Sahayak AI - Mobile App Launcher
echo ========================================
echo.

REM Check Flutter installation
flutter --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Flutter is not installed!
    echo.
    echo Please install Flutter from:
    echo https://flutter.dev/docs/get-started/install
    echo.
    pause
    exit /b 1
)

echo [OK] Flutter is installed
echo.

REM Navigate to mobile app directory
cd /d "%~dp0sahayak_mobile"

if not exist "pubspec.yaml" (
    echo [ERROR] Cannot find mobile app directory!
    echo Expected: %~dp0sahayak_mobile
    pause
    exit /b 1
)

echo [OK] Found mobile app directory
echo.

REM Check if dependencies are installed
if not exist "pubspec.lock" (
    echo [INFO] Installing dependencies...
    flutter pub get
    echo.
)

REM Check for connected devices
echo Checking for connected devices...
flutter devices
echo.

REM Ask user for backend URL
echo.
echo Backend Configuration:
echo ----------------------
echo.
echo Choose your setup:
echo 1. Android Emulator (default: http://10.0.2.2:8000)
echo 2. Physical Device (custom IP)
echo 3. Production Server
echo.

set /p choice="Enter choice (1-3) or press Enter for default [1]: "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo [INFO] Using Android Emulator configuration
    echo Backend URL: http://10.0.2.2:8000
    echo.
    flutter run
) else if "%choice%"=="2" (
    echo.
    echo Find your PC's IP address using: ipconfig
    echo Look for "IPv4 Address"
    echo.
    set /p pc_ip="Enter your PC's IP address (e.g., 192.168.1.100): "
    echo.
    echo [INFO] Using custom backend URL
    echo Backend URL: http://%pc_ip%:8000
    echo.
    flutter run --dart-define=API_BASE_URL=http://%pc_ip%:8000
) else if "%choice%"=="3" (
    echo.
    set /p prod_url="Enter production URL (e.g., https://api.sahayak.ai): "
    echo.
    echo [INFO] Using production server
    echo Backend URL: %prod_url%
    echo.
    flutter run --dart-define=API_BASE_URL=%prod_url%
) else (
    echo [ERROR] Invalid choice!
    pause
    exit /b 1
)

echo.
echo ========================================
echo        App Running Successfully!
echo ========================================
echo.
echo Tips:
echo - Press 'r' for hot reload
echo - Press 'R' for hot restart  
echo - Press 'q' to quit
echo.

pause
