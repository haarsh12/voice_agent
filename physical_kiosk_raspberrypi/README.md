# Sahayak AI — Raspberry Pi Physical Kiosk

Production-grade hardware kiosk that runs the **exact same React frontend** as the website, served from a local Flask server that proxies all backend API calls with `X-Sahayak-Device: raspberrypi`.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Raspberry Pi                        │
│                                                     │
│  ┌───────────────┐     ┌──────────────────────────┐ │
│  │  Chromium     │────▶│  kiosk_server.py (Flask) │ │
│  │  (full-screen)│◀────│  Port 5000               │ │
│  └───────────────┘     └──────────┬───────────────┘ │
│                                   │ proxy + header  │
│  ┌───────────┐  ┌───────────┐     │ X-Sahayak-     │
│  │  ALSA Mic │  │  Camera   │     │ Device:        │
│  │  Speaker  │  │  (MJPEG)  │     │ raspberrypi    │
│  └───────────┘  └───────────┘     │                │
└───────────────────────────────────┼────────────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  Sahayak AI Backend    │
                       │  FastAPI  Port 8000    │
                       │  + LiveKit Voice Agent │
                       └────────────────────────┘
```

**The React app in `static/` is the exact same code as the website** — same design, same components (Schemes, Grievances, Knowledge Base, Admin, Voice, Auth, etc.) — just compiled with `VITE_CLIENT_DEVICE=raspberrypi` so every API call is tagged as coming from the physical kiosk.

---

## 📁 File Structure

```text
physical_kiosk_raspberrypi/
├── kiosk_server.py       # Flask: serves React UI + proxies all /api/* to backend
├── audio_capture.py      # ALSA mic VAD & push-to-talk
├── stt_service.py        # Google Cloud STT (hardware mic fallback)
├── face_service.py       # OpenCV face detection / recognition
├── config.py             # Env loader — all settings from config.env
├── config.env            # ← Edit this: set BACKEND_SERVER_URL
├── requirements.txt      # Python dependencies
├── build_kiosk_ui.bat    # Windows: rebuild the React UI
├── start_kiosk.sh        # Chromium fullscreen autostart
├── setup_kiosk.sh        # Systemd + autostart installer
└── static/               # Built React app (run build_kiosk_ui.bat to generate)
    ├── index.html
    └── assets/
        ├── index-*.js
        ├── index-*.css
        └── VoiceExperience-*.js
```

---

## 🚀 Setup Instructions

### Step 1 — Configure backend IP
Edit `config.env`:
```ini
BACKEND_SERVER_URL=http://<YOUR_BACKEND_IP>:8000
LIVEKIT_AGENT_NAME=sahayak-ai
```

### Step 2 — Build the React UI (on Windows dev machine)
```bat
build_kiosk_ui.bat
```
Or manually:
```powershell
cd frontend
npm run build:kiosk
```
This compiles the React app to `physical_kiosk_raspberrypi/static/`.

### Step 3 — Copy to Raspberry Pi
```bash
scp -r physical_kiosk_raspberrypi/ pi@raspberrypi.local:~/sahayak/
```

### Step 4 — Install Python dependencies on Pi
```bash
cd ~/sahayak/physical_kiosk_raspberrypi
pip3 install -r requirements.txt
```

### Step 5 — Run and enable autostart
```bash
chmod +x setup_kiosk.sh start_kiosk.sh
./setup_kiosk.sh
```
This installs a systemd service for `kiosk_server.py` and configures Chromium to open `http://localhost:5000` full-screen on boot.

### Manual run (for testing)
```bash
python3 kiosk_server.py
# Then open http://localhost:5000 in any browser to preview
```

---

## 🌟 Features on Kiosk Screen

All features are identical to the website because it IS the website code:

| Feature | Status |
|---|---|
| Voice AI (LiveKit WebRTC) | ✅ Full |
| Schemes Catalogue | ✅ Full |
| Grievance Center | ✅ Full |
| Knowledge Base | ✅ Full |
| Admin Panel | ✅ Full |
| Auth / Sign-in / WebAuthn | ✅ Full |
| Account Creation / Onboarding | ✅ Full |
| Document Upload + Camera Scan | ✅ Full |
| 10 Indian Languages | ✅ Full |
| Dark/Light mode, all animations | ✅ Full |

---

## 🔄 Updating the UI

Whenever you make changes to the React frontend:
1. Run `build_kiosk_ui.bat` on Windows
2. Copy the new `static/` folder to the Pi (or `rsync`)
3. Restart: `sudo systemctl restart sahayak-kiosk.service`
