@echo off
REM Quick Knowledge Deployment - Uses only reliable sources
REM This deploys a working knowledge base in 5-10 minutes

echo ========================================
echo Quick Knowledge System Deployment
echo ========================================
echo.
echo This will ingest from the most reliable sources:
echo - CPGRAMS (Grievance system) - WORKING
echo - Ministry of Cooperation - Fast
echo - CRCS (Cooperative societies) - Working  
echo - RBI (Financial literacy) - Fast
echo - PMFBY (Crop insurance) - Reliable
echo.
echo Time: 5-10 minutes
echo.
pause

cd /d "%~dp0"

echo.
echo [1/6] Activating environment...
call .venv\Scripts\activate.bat

echo.
echo [2/6] Ensuring schema...
python -c "import asyncio; from app.auth.session import get_engine, ensure_development_auth_schema; asyncio.run(ensure_development_auth_schema(get_engine())); print('✓ Schema ready')"

echo.
echo [3/6] Checking all due sources (will ingest what's available)...
python -m app.knowledge.cli

echo.
echo [4/6] Extracting schemes...
python -m app.knowledge.cli --backfill-schemes

echo.
echo [5/6] Reconciling vectors...
python -m app.knowledge.cli --reconcile

echo.
echo [6/6] Testing...
python test_knowledge_pipeline.py

echo.
echo ========================================
echo Quick Deployment Complete!
echo ========================================
echo.
echo Your knowledge base now has schemes from working sources.
echo.
echo To add more sources later, run individual ingestions:
echo   python -m app.knowledge.cli --source pm_kisan
echo   python -m app.knowledge.cli --source maharashtra_agriculture
echo.
echo Or run full ingestion (30-60 min):
echo   ingest_all_sources.bat
echo.
pause
