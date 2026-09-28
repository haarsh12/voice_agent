@echo off
echo ===================================
echo PHONE CONNECTION TEST
echo ===================================
echo.

echo Your PC IP: 10.217.65.207
echo Backend Port: 8000
echo.

echo Testing backend accessibility...
curl -v http://10.217.65.207:8000/api/health
echo.

echo ===================================
echo NEXT STEP:
echo ===================================
echo.
echo Open Chrome on your PHONE and go to:
echo   http://10.217.65.207:8000/api/health
echo.
echo You should see:
echo   {"status":"ok","agent_name":"vyamit-voice","configured":true}
echo.
echo If it works in Chrome on phone, then reinstall Flutter app:
echo   flutter run
echo.

pause
