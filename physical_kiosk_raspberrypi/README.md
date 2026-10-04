# Sahayak AI — Raspberry Pi Physical Kiosk

Production-grade hardware integration codebase for running the **Sahayak AI Touch Screen Kiosk** on a Raspberry Pi. 
It features a full-screen, touch-optimized Chromium UI that mirrors the frontend website's design, running alongside 
background hardware processes.

## 🌟 Upgraded Capabilities
- **Touch-Optimized Frontend Mirror:** Pure HTML/JS implementation of the React frontend UI, styled with the same CSS variables, perfectly scaled for a 1024x600 touch screen.
- **LiveKit Voice Integration:** The kiosk UI connects seamlessly to the Sahayak AI LiveKit voice agent using a proxied token.
- **Document Scanning:** Integrated camera capture in the UI for snapping documents and sending them to the backend API.
- **API Proxying:** The local Flask server proxies all backend calls (adding `X-Sahayak-Device: raspberrypi`) so the backend URL and LiveKit tokens are never exposed in the browser source.
- **Simultaneous Multi-Hardware:** Runs OpenCV face recognition HUD, ALSA microphone push-to-talk (fallback), and speaker TTS concurrently without blocking.

---

## 📁 File Structure

```text
sahayak_ai/
└── physical_kiosk_raspberrypi/
    ├── config.py             # Centralized hardware configuration loader
    ├── config.env            # Environment variables (Backend IP, ALSA devices)
    ├── kiosk_server.py       # Production Flask server, Backend Proxy & hardware gateway
    ├── audio_capture.py      # Dual ALSA audio recorder (USB mic / INMP441 I2S)
    ├── stt_service.py        # Google Cloud Speech-to-Text engine (fallback)
    ├── face_service.py       # OpenCV YuNet & SFace real-time face detection/recognition
    ├── start_kiosk.sh        # Chromium auto-launch in full-screen touch kiosk mode
    ├── setup_kiosk.sh        # Systemd & desktop autostart installer script
    ├── requirements.txt      # Python dependencies
    └── templates/
        └── index.html        # Touch Screen Web UI (LiveKit + Document Scan + Services)
```

---

## 🚀 Quick Setup Instructions

1. **Install Dependencies**:
   ```bash
   cd sahayak_ai/physical_kiosk_raspberrypi
   pip3 install -r requirements.txt
   chmod +x setup_kiosk.sh start_kiosk.sh
   ```

2. **Set Backend IP Address**:
   Edit `config.env` and update `BACKEND_SERVER_URL` with your central backend server IP:
   ```ini
   BACKEND_SERVER_URL=http://<YOUR_BACKEND_IP>:8000
   LIVEKIT_AGENT_NAME=sahayak-ai
   ```

3. **Run Kiosk Server Manually**:
   ```bash
   python3 kiosk_server.py
   ```
   *Navigate to `http://localhost:5000` to preview the kiosk UI.*

4. **Enable Boot Autostart & Launch Kiosk Mode**:
   ```bash
   ./setup_kiosk.sh
   ```
   *This enables the `sahayak-kiosk.service` and configures Chromium to start full-screen on boot.*
