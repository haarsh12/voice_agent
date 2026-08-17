@echo off
echo ===================================
echo PHONE CONNECTIVITY DIAGNOSTIC
echo ===================================
echo.

echo 1. Checking your PC IP address...
ipconfig | findstr /C:"IPv4"
echo.

echo 2. Testing if backend is running locally...
curl http://localhost:8000/api/health
echo.

echo 3. Checking what interfaces backend is listening on...
netstat -an | findstr ":8000"
echo.

echo 4. Checking Windows Firewall rules for port 8000...
netsh advfirewall firewall show rule name=all | findstr /C:"8000" /C:"Rule Name"
echo.

echo ===================================
echo INSTRUCTIONS FOR PHONE TEST:
echo ===================================
echo.
echo 1. Make sure phone is on SAME WiFi as PC
echo 2. On your phone, open Chrome browser
echo 3. Go to: http://10.217.65.207:8000/api/health
echo 4. You should see JSON response
echo.
echo If you get "can't reach" or timeout:
echo   - Run: allow_port_8000.bat as Administrator
echo   - Check phone WiFi settings (should be same network)
echo   - Disable VPN on phone if enabled
echo.

pause
