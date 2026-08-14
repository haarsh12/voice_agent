@echo off
echo ========================================
echo Testing Backend Network Accessibility
echo ========================================
echo.

echo 1. Checking if backend is running locally...
curl -s http://127.0.0.1:8000/api/health
echo.
echo.

echo 2. Checking if backend is accessible on network IP...
curl -s http://10.24.124.207:8000/api/health
echo.
echo.

echo 3. Checking Windows Firewall rules for port 8000...
netsh advfirewall firewall show rule name=all | findstr "8000"
echo.
echo.

echo 4. Checking what IP addresses the backend is listening on...
netstat -an | findstr ":8000"
echo.
echo.

echo ========================================
echo Test Complete
echo ========================================
echo.
echo INSTRUCTIONS:
echo 1. If test 1 works but test 2 fails, Windows Firewall is blocking
echo 2. If both fail, backend is not running
echo 3. If netstat shows 127.0.0.1:8000, backend is only listening locally
echo 4. Backend should show 0.0.0.0:8000 to accept external connections
echo.
pause
