@echo off
REM ============================================================
REM  Sahayak AI — Build Kiosk UI
REM  Run this on your Windows dev machine whenever you update
REM  the frontend. Then copy the static/ folder to the Pi.
REM ============================================================

echo [1/2] Installing / updating dependencies...
cd /d "%~dp0..\frontend"
call npm install

echo.
echo [2/2] Building React app for kiosk (X-Sahayak-Device: raspberrypi)...
call npm run build:kiosk

echo.
echo ============================================================
echo  Build complete!  static/ folder is ready.
echo  On the Raspberry Pi just restart kiosk_server.py.
echo ============================================================
pause
