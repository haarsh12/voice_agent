@echo off
REM Script to package secret files for sharing with team members
REM This creates a password-protected zip file with all necessary secrets

echo ========================================
echo Package Secrets for Team Sharing
echo ========================================
echo.

REM Check if files exist
if not exist "backend\.env" (
    echo ERROR: backend\.env not found!
    pause
    exit /b 1
)

if not exist "backend\project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json" (
    echo ERROR: backend\project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json not found!
    pause
    exit /b 1
)

if not exist "frontend\.env" (
    echo ERROR: frontend\.env not found!
    pause
    exit /b 1
)

echo All required files found!
echo.
echo Files to be packaged:
echo  - backend\.env
echo  - backend\project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json
echo  - frontend\.env
echo.

REM Create a temporary directory
set TEMP_DIR=secrets_package_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TEMP_DIR=%TEMP_DIR: =0%
mkdir "%TEMP_DIR%"

REM Create directory structure
mkdir "%TEMP_DIR%\backend"
mkdir "%TEMP_DIR%\frontend"

REM Copy files
echo Copying files...
copy "backend\.env" "%TEMP_DIR%\backend\.env" >nul
copy "backend\project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json" "%TEMP_DIR%\backend\project-d8fe05cb-90bb-4815-aca-c79b84dcbad5.json" >nul
copy "frontend\.env" "%TEMP_DIR%\frontend\.env" >nul
copy "SETUP_FOR_NEW_DEVELOPERS.md" "%TEMP_DIR%\SETUP_INSTRUCTIONS.md" >nul

echo.
echo ========================================
echo IMPORTANT: Password Protection
echo ========================================
echo.
echo This script has created a folder with your secret files.
echo You need to manually create a PASSWORD-PROTECTED zip file.
echo.
echo Steps:
echo 1. Right-click the folder: %TEMP_DIR%
echo 2. Send to ^> Compressed (zipped) folder
echo 3. Use 7-Zip or WinRAR to add password protection
echo.
echo Folder location: %cd%\%TEMP_DIR%
echo.
echo SECURITY REMINDERS:
echo - Use a STRONG password (at least 16 characters)
echo - Send password via DIFFERENT channel (SMS/WhatsApp)
echo - Delete the folder after creating the zip
echo - Delete the zip after recipient confirms receipt
echo.

explorer "%TEMP_DIR%"

echo.
echo Folder opened in Explorer.
echo Create a password-protected zip, then DELETE this folder!
echo.
pause

REM Ask if user wants to delete the folder
echo.
set /p DELETE_FOLDER="Delete the temporary folder now? (y/n): "
if /i "%DELETE_FOLDER%"=="y" (
    rmdir /s /q "%TEMP_DIR%"
    echo Folder deleted!
) else (
    echo Remember to delete "%TEMP_DIR%" after creating the zip!
)

echo.
echo Done!
pause
