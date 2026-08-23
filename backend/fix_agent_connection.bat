@echo off
echo =========================================================
echo  Fixing LiveKit Agent Connection Issues
echo =========================================================
echo.

echo Step 1: Testing connectivity...
call .venv\Scripts\activate
python diagnose_connectivity.py

echo.
echo =========================================================
echo Step 2: Testing LiveKit credentials...
python -c "from app.config.settings import get_settings; s = get_settings(); print('LiveKit URL:', s.livekit_url); print('Agent Name:', s.agent_name); print('Credentials:', 'OK' if s.livekit_api_key and s.livekit_api_secret else 'MISSING')"

echo.
echo =========================================================
echo Step 3: Testing providers...
python -c "from app.agent.providers import create_tts, create_stt, create_llm; from app.config.settings import get_settings; s = get_settings(); create_tts(s); create_stt(s); create_llm(s); print('All providers: OK')"

echo.
echo =========================================================
echo  Diagnosis Complete!
echo =========================================================
echo.
echo If connectivity tests passed but agent still fails:
echo.
echo 1. Add firewall exception for Python:
echo    - Windows Settings ^> Firewall ^> Allow app
echo    - Add: .venv\Scripts\python.exe
echo.
echo 2. Try mobile hotspot to bypass network restrictions
echo.
echo 3. Temporarily disable antivirus
echo.
echo 4. Check if running behind corporate firewall/VPN
echo.
echo Ready to start agent? Press any key...
pause >nul

echo.
echo Starting agent...
python -m app.agent.runner dev
