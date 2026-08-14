@echo off
echo ========================================
echo Adding Windows Firewall Rule for Port 8000
echo ========================================
echo.
echo This will allow incoming connections on port 8000
echo Run this as Administrator!
echo.
pause

netsh advfirewall firewall add rule name="Backend API Port 8000" dir=in action=allow protocol=TCP localport=8000

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Firewall rule added!
    echo Port 8000 is now open for incoming connections.
    echo.
    echo Your phone should now be able to reach: http://10.24.124.207:8000
) else (
    echo.
    echo ERROR: Failed to add firewall rule.
    echo Please right-click this file and select "Run as Administrator"
)

echo.
pause
