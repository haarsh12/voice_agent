# Sahayak AI — Raspberry Pi Kiosk Terminal & Hardware Interface

Production-grade hardware integration codebase for running the **Sahayak AI Touch Screen Kiosk** on a Raspberry Pi. Simultaneously manages camera face recognition HUD, microphone voice capture (VAD & Push-to-Talk button), speaker text-to-speech output, and touch screen kiosk Web UI.

---

## 📁 Architecture & File Structure

```text
sahayak_ai/
└── raspberrypi_screen/
    ├── config.py             # Centralized hardware configuration loader
    ├── config.env            # Environment variables (Backend IP, ALSA devices)
    ├── kiosk_server.py       # Production Flask server & hardware gateway
    ├── audio_capture.py      # Dual ALSA audio recorder (USB mic / INMP441 I2S)
    ├── stt_service.py        # Google Cloud Speech-to-Text engine
    ├── face_service.py       # OpenCV YuNet & SFace real-time face detection/recognition
    ├── start_kiosk.sh        # Chromium auto-launch in full-screen touch kiosk mode
    ├── setup_kiosk.sh        # Systemd & desktop autostart installer script
    ├── requirements.txt      # Python dependencies
    └── templates/
        └── index.html        # Glassmorphic Touch Screen Web UI
```

---

## ⚡ Key Features

1. **Simultaneous Multi-Hardware Execution**: Runs camera face scanning, microphone listening, speaker audio playback, and touch display rendering concurrently without blocking main threads.
2. **Dynamic Backend Server Connection**: Connects to the backend via configurable `BACKEND_SERVER_URL` in `config.env`.
3. **Chromium Full-screen Kiosk Integration**: Includes `start_kiosk.sh` with touch events enabled, auto-play permission flags, and hidden mouse cursors for physical kiosk hardware.
4. **Resilient System Service**: Includes systemd `sahayak-kiosk.service` generation script for boot autostart and restart resilience.

---

## 🚀 Quick Setup Instructions

1. **Install Dependencies & Hardware Setup**:
   ```bash
   cd sahayak_ai/raspberrypi_screen
   pip3 install -r requirements.txt
   chmod +x setup_kiosk.sh start_kiosk.sh
   ```

2. **Set Backend IP Address**:
   Edit `config.env` and update `BACKEND_SERVER_URL` with your backend server IP:
   ```ini
   BACKEND_SERVER_URL=http://<YOUR_BACKEND_IP>:5000
   ```

3. **Run Kiosk Server Manually**:
   ```bash
   python3 kiosk_server.py
   ```

4. **Enable Boot Autostart & Launch Kiosk Mode**:
   ```bash
   ./setup_kiosk.sh
   ```
