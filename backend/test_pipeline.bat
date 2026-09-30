@echo off
REM Quick test script for knowledge pipeline validation

echo ====================================
echo Knowledge Pipeline Validation Test
echo ====================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Running tests...
echo.

python test_knowledge_pipeline.py

echo.
pause
