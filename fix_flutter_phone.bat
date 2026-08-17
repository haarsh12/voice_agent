@echo off
echo ========================================
echo FLUTTER PHONE CONNECTION FIX
echo ========================================
echo.

echo Step 1: Getting your PC IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do set IP=%%a
set IP=%IP:~1%
echo Your PC IP: %IP%
echo.

echo Step 2: Checking backend status...
curl http://localhost:8000/api/health 2>nul
if errorlevel 1 (
    echo ❌ Backend not running!
    echo Please start: start_complete_backend.bat
    pause
    exit /b 1
)
echo ✅ Backend running
echo.

echo Step 3: Test from network IP...
curl http://%IP%:8000/api/health 2>nul
if errorlevel 1 (
    echo ❌ Backend not accessible on network!
    echo This might be a firewall issue.
    echo Running firewall fix...
    netsh advfirewall firewall add rule name="Backend API Port 8000" dir=in action=allow protocol=TCP localport=8000
)
echo ✅ Backend accessible on network
echo.

echo ========================================
echo WHAT TO DO NOW:
echo ========================================
echo.
echo 1. On your phone, make sure you're on SAME WiFi as PC
echo.
echo 2. Open Chrome on your phone and test:
echo    http://%IP%:8000/api/health
echo.
echo 3. If Chrome works, rebuild Flutter app:
echo    cd android_app
echo    flutter run
echo.
echo 4. Once app opens, tap the network icon (top right)
echo    to run diagnostics
echo.

pause
