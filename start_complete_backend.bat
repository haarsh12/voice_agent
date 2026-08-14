@echo off
echo ===================================
echo Starting Complete Vyamit Voice Backend
echo ===================================
echo.
echo This will start:
echo 1. FastAPI backend server (port 8000)
echo 2. LiveKit agent worker
echo.
echo Press Ctrl+C to stop both services
echo.

cd backend
call .venv\Scripts\activate.bat

echo [1/2] Starting FastAPI backend server...
start "Vyamit Backend API" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo [2/2] Starting LiveKit agent worker...
start "Vyamit Agent Worker" cmd /k "python -m app.agent.runner start"

echo.
echo ===================================
echo ✅ Both services started!
echo ===================================
echo.
echo Access points:
echo - Frontend: http://localhost:5173
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Agent Worker: Running in background
echo.
echo To stop: Close the terminal windows
echo ===================================
