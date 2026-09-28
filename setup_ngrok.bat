@echo off
echo ========================================
echo NGROK SETUP GUIDE
echo ========================================
echo.
echo Ngrok creates a public URL for your backend
echo so your phone can access it from anywhere.
echo.
echo STEP 1: Download ngrok
echo ----------------------------------------
echo 1. Go to: https://ngrok.com/download
echo 2. Download "Windows (64-bit)" version
echo 3. Extract ngrok.exe to this folder: D:\voice_stream
echo.
pause
echo.
echo STEP 2: Sign up and get auth token
echo ----------------------------------------
echo 1. Go to: https://dashboard.ngrok.com/signup
echo 2. Sign up (free account)
echo 3. Copy your auth token from dashboard
echo.
pause
echo.
echo STEP 3: Setup auth token
echo ----------------------------------------
set /p TOKEN="Paste your ngrok auth token here: "
ngrok config add-authtoken %TOKEN%
echo.
echo STEP 4: Start ngrok tunnel
echo ----------------------------------------
echo Now run: ngrok http 8000
echo.
echo This will give you a URL like:
echo   https://xxxx-xxxx-xxxx.ngrok-free.app
echo.
echo Copy that URL and I'll update your Flutter app!
echo.
pause
