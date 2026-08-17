@echo off
echo ========================================
echo NGROK TUNNEL SETUP
echo ========================================
echo.

echo Step 1: Configuring auth token...
ngrok config add-authtoken cr_3I2AngCmnAB7dQDMOtxePhU2ySv
echo.

echo Step 2: Starting tunnel on port 8000...
echo.
echo ⚠️  IMPORTANT:
echo    - Copy the "Forwarding" HTTPS URL you see below
echo    - It will look like: https://xxxx-xxxx.ngrok-free.app
echo    - Share this URL with me to update Flutter app
echo    - Keep this window OPEN while using the app
echo.
pause
echo.

ngrok http 8000
