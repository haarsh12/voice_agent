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

## Verified Knowledge Engine

The data engine is intentionally server-owned and source-grounded. It replaces
the former keyword-to-link catalogue: a source card is returned only when the
answer has retrieved a current chunk from a reviewed source document.

    approved source registry
      → scheduled incremental check (separate worker)
      → fetch + validate + hash changed content only
      → extract + semantic chunk
      → embed + Qdrant index
      → relational version/freshness validation
      → Gemini explanation + real citation

The initial registry contains exactly the ten approved source groups from the
project brief: Ministry of Cooperation, National Cooperative Database, CRCS,
India Code, State RCS / Cooperative Departments, PMFBY, Ministry of
Agriculture & Farmers Welfare, myScheme, RBI, and CPGRAMS. Each source has a
reviewed entry page and path-scoped, one-hop discovery adapter for circulars,
notifications, guidelines, and formal documents. The worker does not crawl
arbitrary outbound links, search results, social media, or user-provided web
pages.

The online chat path does not fetch or ingest documents. It searches only the
backend-configured Qdrant collection, then verifies each result against the
PostgreSQL document lifecycle before it can be cited. CURRENT versions are
eligible; EXPIRED and SUPERSEDED versions are not. Scheme, legal, financial,
deadline, eligibility, claim, procedure, contact, and notification requests
without current verified evidence receive a transparent abstention rather than
a model-generated official-looking answer.

### Deploying the knowledge engine

1. Apply [20260928_add_verified_knowledge_engine.sql](/D:/voice_stream/supabase/migrations/20260928_add_verified_knowledge_engine.sql) and then [20260929_add_knowledge_coverage_metadata.sql](/D:/voice_stream/supabase/migrations/20260929_add_knowledge_coverage_metadata.sql) after the existing account migrations.
2. Configure `QDRANT_URL`, optional `QDRANT_API_KEY`,
   `QDRANT_COLLECTION`, `GOOGLE_APPLICATION_CREDENTIALS`, and
   `KNOWLEDGE_EMBEDDING_MODEL` in the backend deployment secret store. To OCR
   scanned PDFs, enable Google Cloud Vision for the configured service account
   and set `KNOWLEDGE_OCR_PROVIDER=google_cloud_vision`. Do not put any of
   them in `frontend/.env` or a `VITE_` variable.
3. Run a separate scheduled worker, for example:

       cd backend
       .\.venv\Scripts\python.exe -m app.knowledge.cli

   The worker uses the registry's individual intervals: daily for dynamic
   sources, weekly for National Cooperative Database and India Code. It sends
   conditional requests when ETag/Last-Modified metadata exists and only
   chunks, embeds, and indexes changed document hashes. An operator can run
   one reviewed source explicitly with `-m app.knowledge.cli --source pmfby`.
   Use `-m app.knowledge.cli --reconcile` after a Qdrant incident to repair
   only missing or stale derived vector points, or `--reindex-source pmfby`
   after an approved embedding-model change.

Qdrant credentials, source content, ingestion diagnostics, and database
records remain server-side. The browser receives only the answer, its evidence
status, and citation metadata needed to open the source document. LiveKit voice
turns use the same retrieval path; the agent never speaks citations or URLs,
while the browser displays verified source links underneath the voice reply.

### Knowledge Base and administrator access

`/knowledge-base` is a public transparency view. It lists the reviewed source
registry, official entry links, update outcomes, document-version metadata,
extraction method, and safe aggregate index counts. Its API deliberately
excludes document text, chunks, embeddings, hashes, database details, provider
endpoints, credentials, and member data. The endpoint is rate-limited and its
Qdrant readiness probe is cached briefly so the page cannot become an index
probing surface.

`/admin` is a separate, rate-limited administrator sign-in only. It has an
independent HttpOnly, SameSite cookie and CSRF-protected logout. Configure an
Argon2id `ADMIN_PASSWORD_HASH` in the deployment secret store; never store or
commit the administrator password. Private administration tools can be added
behind this boundary in a later release.

The desktop voice workspace grows naturally while the conversation is short,
then caps its transcript card at two viewport lengths. Further entries scroll
inside that card without forcing the full page to grow or interrupting a
member who has scrolled back through the conversation.

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
