@echo off
REM Run script for Sahayak Mobile Flutter App

echo ========================================
echo Sahayak Mobile - Running App
echo ========================================
echo.

echo Checking for connected devices...
flutter devices
echo.

echo Starting Flutter app...
echo.
echo Controls:
echo - Press 'r' for hot reload
echo - Press 'R' for hot restart
echo - Press 'q' to quit
echo.

flutter run

pause
