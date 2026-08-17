@echo off
echo ========================================
echo NGROK TUNNEL FOR PHONE ACCESS
echo ========================================
echo.
echo This creates a public URL for your backend
echo that your phone can access from anywhere.
echo.
echo 1. Install ngrok from: https://ngrok.com/download
echo 2. Sign up and get auth token
echo 3. Run: ngrok http 8000
echo.
echo This will give you a URL like:
echo https://xxxx-xxxx-xxxx.ngrok-free.app
echo.
echo Update android_app/lib/services/api_service.dart:
echo   static const String baseUrl = 'https://your-ngrok-url';
echo.
echo Restart Flutter app and it will work!
echo.
pause
