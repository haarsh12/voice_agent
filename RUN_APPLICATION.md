# Run Sahayak AI locally

## Start the app

Use two terminals:

    # Terminal 1 — FastAPI
    cd backend
    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

    # Terminal 2 — React
    cd frontend
    npm.cmd install
    npm.cmd run dev

Then open the address displayed by Vite, usually http://localhost:5173.

For voice conversations, also start the LiveKit worker:

    cd backend
    .\.venv\Scripts\python.exe -m app.agent.runner start

The included Windows shortcuts start the same services:

- start_backend.bat — FastAPI service
- start_frontend.bat — Vite development server
- start_complete_backend.bat — FastAPI plus the LiveKit worker

## Required server configuration

Copy .env.example to .env and configure the existing LiveKit and Google
credentials. The agent name must match for the FastAPI token service and the
worker:

    AGENT_NAME=sahayak-ai
    VITE_AGENT_NAME=sahayak-ai

The React app talks to FastAPI at http://127.0.0.1:8000 by default. If Vite
runs at an address not included in CORS_ORIGINS, add that explicit local
origin to the server environment and restart FastAPI.

## Mobile account testing

Before testing the sign-in flow, apply
supabase/migrations/20260914_sahayak_account_data.sql to the server database
and configure:

    DATABASE_URL=postgresql://...
    JWT_SECRET_KEY=a-long-random-server-secret
    OTP_DEMO_MODE=true
    OTP_DEMO_CODE=624251

During development, FastAPI accepts the demo OTP 624251. It is never placed in
the React app. Production startup fails closed when OTP_DEMO_MODE=true; disable
it and configure an SMS provider before any real deployment.

## Verify

    cd frontend
    npm.cmd run build

    cd ..\backend
    .\.venv\Scripts\python.exe -m pytest -q

Expected API readiness endpoint: http://127.0.0.1:8000/api/health
