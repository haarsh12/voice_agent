# Sahayak AI

Sahayak AI is a multilingual, voice-first web platform for cooperative
members, farmers and rural stakeholders. It is being developed for SIH problem
statement 26088: **Multilingual Cooperative Governance & Legal Assistance
Chatbot**.

## What works in this phase

- A white, premium, responsive web experience with public landing and voice
  workspace.
- Ten-language voice and text interaction: Hindi, Marathi, English, Tamil,
  Telugu, Kannada, Malayalam, Gujarati, Bengali and Punjabi.
- Existing LiveKit voice flow, selected-language STT/TTS, typed chat,
  interruption handling and safe in-memory guest context.
- Safe document discussion in the voice workspace for PDF, DOCX, text and
  common image files. Guest content stays in memory and expires.
- Mobile-number OTP UI, backend-owned JWT session cookies, profile onboarding
  and logout revocation.
- Optional device Face ID / biometric sign-in through WebAuthn passkeys. The
  device performs biometric matching; Sahayak stores no face photo, template,
  embedding or private key.
- Guest mode: voice and language selection remain available; Dashboard,
  Documents, Schemes, Notifications, Grievances and Profile visibly prompt
  guests to sign in.
- Clearly marked preview UI for services that await approved backend/data
  integrations. It does not present invented scheme or legal information.

## Architecture

    React + TypeScript (Vite)
      ├─ public landing, language control and LiveKit client
      ├─ mobile OTP / profile UI and route-level UX guards
      └─ one API client; no direct database or authentication access
                      │
                      ▼
    FastAPI
      ├─ LiveKit browser-token and guest-session endpoints
      ├─ mobile OTP hashing, expiry, attempt limits and SMS delivery
      ├─ WebAuthn public-credential verification and one-use challenges
      ├─ HttpOnly JWT session cookie + CSRF validation + logout invalidation
      ├─ account/profile authorization
      └─ existing Vertex/LiveKit voice and document-query services

The frontend never signs JWTs, verifies OTPs, holds database credentials or
contains SMS-provider credentials. A SQL migration for the server-owned
account tables is in supabase/migrations/20260914_sahayak_account_data.sql.
It is compatible with a Supabase-hosted Postgres database, but browser-side
Supabase Auth and direct browser database access are intentionally not used.

## Configuration

Copy .env.example to an ignored .env and supply actual server credentials. Key
development settings:

    AGENT_NAME=sahayak-ai
    VITE_AGENT_NAME=sahayak-ai
    DATABASE_URL=postgresql://...
    JWT_SECRET_KEY=a-long-random-server-secret
    OTP_DEMO_MODE=true
OTP_DEMO_CODE=624251
WEB_AUTHN_RP_ID=app.example.in
WEB_AUTHN_ORIGINS=https://app.example.in

The demo OTP is generated and verified only by FastAPI. APP_ENV=production
refuses to start while OTP_DEMO_MODE=true. Disable demo mode and configure an
SMS provider before any real deployment. Never add JWT secrets, database
connection strings, OTP values, service-role keys or provider credentials to
frontend/.env or a VITE_ variable.

Apply the SQL migration with an administrator database connection before using
mobile accounts. It explicitly denies anon and authenticated browser roles
from reading account and OTP tables.

Apply `supabase/migrations/20260927_add_webauthn_face_sign_in.sql` after the
account migration to enable device biometric sign-in in a hosted database.
Set the WebAuthn origin and RP ID to the exact public HTTPS site before
deployment. Face ID setup requires a fresh mobile-OTP verification, stores a
device-specific public credential, expires each challenge after five minutes,
requires local user verification, checks the authenticator counter to detect
cloned credentials, and can be removed from the profile. A member can always
fall back to mobile OTP; biometric matching itself never leaves their device.

The frontend only needs:

    VITE_AGENT_NAME=sahayak-ai
    VITE_API_BASE_URL=http://127.0.0.1:8000

## Run locally

    # Terminal 1
    cd backend
    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

    # Terminal 2
    cd frontend
    npm.cmd install
    npm.cmd run dev

## Safety boundary

Sahayak AI provides educational assistance, not legal representation, financial
advice, insurance approval or an official decision. Current scheme details,
legal provisions, deadlines, eligibility and grievance procedures must come
from reviewed official sources. Until that knowledge layer is connected, the
product labels those areas as previews instead of fabricating content.
