@echo off
echo ========================================
echo Sahayak AI - Phone Connection Setup
echo ========================================
echo.
echo Your laptop IP: 192.168.29.241
echo Backend port: 8000
echo Full URL: http://192.168.29.241:8000
echo.
echo ========================================
echo Step 1: Allow Port 8000 in Firewall
echo ========================================
echo Adding firewall rule for port 8000...
netsh advfirewall firewall delete rule name="Sahayak Backend 8000" >nul 2>&1
netsh advfirewall firewall add rule name="Sahayak Backend 8000" dir=in action=allow protocol=TCP localport=8000
echo Firewall rule added successfully!
echo.
echo ========================================
echo Step 2: Verify Backend is Running
echo ========================================
echo.
echo Opening backend health check in browser...
timeout /t 2 >nul
start http://192.168.29.241:8000/docs
echo.
echo If the page opens, your backend is accessible!
echo If not, make sure backend is running:
echo   cd backend
echo   .\.venv\Scripts\activate
echo   uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo ========================================
echo Step 3: Test from Phone
echo ========================================
echo.
echo On your phone (same WiFi):
echo 1. Open browser: http://192.168.29.241:8000/docs
echo 2. If it works, your phone can connect!
echo 3. Launch Sahayak AI app and test
echo.
echo ========================================
echo Step 4: Rebuild Flutter App
echo ========================================
echo.
echo The API config has been updated to: http://192.168.29.241:8000
echo.
echo Choose an option:
echo [1] Hot Reload (if app is already running)
echo [2] Rebuild and Run
echo [3] Skip
echo.
choice /c 123 /n /m "Enter choice (1-3): "
if errorlevel 3 goto :end
if errorlevel 2 goto :rebuild
if errorlevel 1 goto :reload

:reload
echo.
echo Hot reloading app (save any file in Flutter)...
echo The app will automatically reload with new API URL.
echo.
goto :end

:rebuild
echo.
echo Rebuilding Flutter app...
cd sahayak_mobile
flutter pub get
flutter build apk --debug
echo.
echo Installing on connected device...
flutter install
echo.
goto :end

:end
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Your phone should now be able to connect to:
echo http://192.168.29.241:8000
echo.
echo If connection fails:
echo - Verify both devices on same WiFi
echo - Check laptop firewall allows port 8000
echo - Ensure backend server is running
echo - Test URL in phone browser first
echo.
pause
