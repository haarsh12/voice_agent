@echo off
echo ========================================
echo ADB PORT FORWARDING SETUP
echo ========================================
echo.
echo This creates a tunnel so your phone can
echo reach the backend through USB connection.
echo.

echo Step 1: Connecting phone via ADB...
adb devices
echo.

echo Step 2: Setting up port forward...
echo Phone port 8000 -> Laptop port 8000
adb reverse tcp:8000 tcp:8000
echo.

if %ERRORLEVEL% EQU 0 (
    echo ✅ Port forwarding enabled!
    echo.
    echo Now your Flutter app can use:
    echo   http://localhost:8000
    echo.
    echo Update android_app/lib/services/api_service.dart
    echo Change possibleBaseUrls to:
    echo   ['http://localhost:8000']
    echo.
) else (
    echo ❌ Failed! Make sure:
    echo   1. Phone connected via USB
    echo   2. USB Debugging enabled on phone
    echo   3. ADB installed (comes with Flutter/Android Studio)
)

pause
