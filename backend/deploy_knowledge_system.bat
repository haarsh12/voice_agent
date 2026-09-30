@echo off
REM Complete Knowledge System Deployment Script
REM This runs all necessary steps to populate the knowledge base

echo ========================================
echo Sahayak AI - Knowledge System Deployment
echo ========================================
echo.
echo This will:
echo 1. Create/update database schema
echo 2. Ingest critical sources (fast subset)
echo 3. Extract schemes
echo 4. Verify results
echo.
echo Estimated time: 10-15 minutes
echo.
pause

cd /d "%~dp0"

echo.
echo [Step 1/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [Step 2/5] Ensuring database schema exists...
python -c "import asyncio; from app.auth.session import get_engine, ensure_development_auth_schema; asyncio.run(ensure_development_auth_schema(get_engine())); print('✓ Schema ready')"

echo.
echo [Step 3/5] Ingesting critical sources (Priority: NCDC, PM-KISAN, PMFBY, Cooperatives)...
echo This will take 10-15 minutes...
echo.

REM Ingest critical sources one by one with progress
echo [3.1] NCDC - Cooperative financing schemes...
python -m app.knowledge.cli --source ncdc

echo [3.2] PM-KISAN - Direct income support...
python -m app.knowledge.cli --source pm_kisan

echo [3.3] PMFBY - Crop insurance...
python -m app.knowledge.cli --source pmfby

echo [3.4] Ministry of Cooperation - PACS schemes...
python -m app.knowledge.cli --source ministry_of_cooperation

echo [3.5] CRCS - Cooperative societies regulation...
python -m app.knowledge.cli --source central_registrar_of_cooperative_societies

echo [3.6] Maharashtra Agriculture - State schemes...
python -m app.knowledge.cli --source maharashtra_agriculture

echo [3.7] Ministry of Fisheries - PMMSY...
python -m app.knowledge.cli --source ministry_of_fisheries

echo [3.8] Animal Husbandry - Livestock schemes...
python -m app.knowledge.cli --source department_animal_husbandry_dairying

echo [3.9] Food Processing - PMFME, Sampada...
python -m app.knowledge.cli --source food_processing_ministry

echo [3.10] TRIFED - Van Dhan Vikas...
python -m app.knowledge.cli --source trifed

echo.
echo [Step 4/5] Extracting schemes from ingested documents...
python -m app.knowledge.cli --backfill-schemes

echo.
echo [Step 5/5] Verifying results...
python test_knowledge_pipeline.py

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Check the test results above
echo 2. Open frontend and test voice queries
echo 3. Verify citations appear with URLs
echo.
echo To ingest remaining sources later:
echo   python -m app.knowledge.cli --ingest-all
echo.
pause
