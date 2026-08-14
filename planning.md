# Vyamit Voice Test Lab Plan

## Phase 1 — Backend foundation (current)

1. Keep the LiveKit reference folders read-only and separate from the test app.
2. Complete the Python virtual-environment based backend with typed environment settings, CORS, health checks, safe logs, and a short-lived token API.
3. Dispatch only the configured `vyamit-voice` agent from issued tokens; no provider keys or LiveKit secret can reach the browser.
4. Configure the streaming Deepgram Nova-3 → Mistral → Cartesia Sonic agent, language-aware TTS selection, LiveKit turn handling, barge-in, aligned transcripts, and session/usage logs.
5. Validate imports, token creation, FastAPI startup, agent construction, and the backend unit tests once the local virtual environment has dependencies installed.

## Phase 2 — Minimal frontend boundary (current)

1. Keep the Vite React scaffold intact.
2. Add only typed calls to the backend health and token APIs plus public `VITE_*` endpoint configuration. No visual voice UI is built in this phase.

## Phase 3 — Voice UI (current)

1. Build the React/TypeScript LiveKit session screen with microphone controls, actual track visualizers, playback, reconnect states, and permissions handling.
2. Render streaming user and agent transcripts with an explicit session state model.
3. Test English, Hindi, Marathi, code-switching, barge-in, echo behavior, reconnects, and measured response latency with real credentials.
