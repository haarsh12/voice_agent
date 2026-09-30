@echo off
REM Bulk ingestion script for all knowledge sources
REM This script ingests all registered sources into Qdrant and Supabase

echo ====================================
echo Sahayak AI - Bulk Knowledge Ingestion
echo ====================================
echo.
echo This will ingest ALL registered sources including:
echo - Ministry of Cooperation schemes
echo - NCDC schemes (Yuva Sahakar, Sahakar Mitra, etc.)
echo - PM-KISAN, KCC, Agriculture Infrastructure Fund
echo - PMKSY, Fisheries schemes, Livestock & Dairy schemes
echo - Food Processing schemes, Tribal welfare schemes
echo - FPO schemes, Maharashtra Agriculture schemes
echo - And all other registered government sources
echo.
echo This process may take 30-60 minutes depending on network speed.
echo.
pause

cd /d "%~dp0"

echo.
echo [1/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [2/3] Running bulk ingestion (this will take a while)...
echo.
python -m app.knowledge.cli --ingest-all

echo.
echo [3/3] Reconciling vector store...
echo.
python -m app.knowledge.cli --reconcile

echo.
echo ====================================
echo Bulk ingestion complete!
echo ====================================
echo.
echo Next steps:
echo 1. Check the logs above for any errors
echo 2. Verify schemes are visible in the frontend
echo 3. Test the voice agent with scheme queries
echo.
pause
