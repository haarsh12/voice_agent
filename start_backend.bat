@echo off
echo ===================================
echo Starting Vyamit Voice Backend
echo ===================================
echo.

cd backend
call .venv\Scripts\activate.bat
echo Backend virtual environment activated
echo Starting server on http://localhost:8000
echo API docs will be at http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
