@echo off
echo ========================================
echo NGROK SETUP AND START
echo ========================================
echo.

REM Check if ngrok exists in current directory
if exist "ngrok.exe" (
    echo ✅ Found ngrok.exe in current directory
    goto :setup
)

REM Check Downloads folder
if exist "%USERPROFILE%\Downloads\ngrok.exe" (
    echo ✅ Found ngrok.exe in Downloads
    echo Copying to project folder...
    copy "%USERPROFILE%\Downloads\ngrok.exe" "ngrok.exe"
    goto :setup
)

echo ❌ ngrok.exe not found!
echo.
echo Please:
echo 1. Download from: https://ngrok.com/download
echo 2. Extract ngrok.exe
echo 3. Put it in: D:\voice_stream\
echo.
pause
exit /b 1

:setup
echo.
echo Setting up auth token...
echo.
ngrok config add-authtoken cr_3I2AngCmnAB7dQDMOtxePhU2ySv
echo.

if %ERRORLEVEL% EQU 0 (
    echo ✅ Auth token configured!
    echo.
    echo Starting ngrok tunnel on port 8000...
    echo.
    echo IMPORTANT: Copy the "Forwarding" URL you see below
    echo It will look like: https://xxxx-xxxx.ngrok-free.app
    echo.
    echo Keep this window open while using the app!
    echo.
    pause
    echo.
    ngrok http 8000
) else (
    echo ❌ Failed to configure auth token
    pause
)
