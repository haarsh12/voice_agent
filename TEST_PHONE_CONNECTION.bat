@echo off
echo ========================================
echo Testing Phone Connection to Backend
echo ========================================
echo.
echo Laptop IP: 192.168.29.241
echo Backend URL: http://192.168.29.241:8000
echo.
echo Opening API docs in browser...
echo If this opens successfully, your phone will be able to connect!
echo.
timeout /t 2 >nul
start http://192.168.29.241:8000/docs
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. If browser opened the API docs:
echo    - Your backend is accessible on the network!
echo    - Test the same URL on your phone's browser
echo.
echo 2. If browser shows error:
echo    - Make sure backend is running:
echo      cd backend
echo      .\.venv\Scripts\activate  
echo      uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
echo 3. Firewall (if needed):
echo    - Run: allow_port_8000.bat as Administrator
echo    - Or manually allow port 8000 in Windows Firewall
echo.
echo 4. Test on phone:
echo    - Open phone browser: http://192.168.29.241:8000/docs
echo    - If it works, launch Sahayak AI app
echo.
pause
