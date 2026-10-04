# Sahayak AI — Raspberry Pi Physical Kiosk Server
#
# What this does:
#   1. Serves the production React build from ./static/ — 100% identical to the website
#   2. Proxies every /api/* call to the central backend with X-Sahayak-Device: raspberrypi
#   3. Optionally runs OpenCV face-recognition HUD (only if ENABLE_FACE_HUD=true)
#   4. Exposes /video_feed (MJPEG) and /api/hardware_status for the UI status bar
#
# Works on both Raspberry Pi (production) and Windows laptop (for UI testing).
#
# Build the React UI first (run on dev machine, re-run after frontend changes):
#   cd frontend && npm run build:kiosk

import time
import logging
import requests
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

import config

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("KioskServer")

# ──────────────────────────────────────────────────────────────────────────────
# Flask app — serves the compiled React build from ./static/
# ──────────────────────────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = Flask(__name__, static_folder=None)

# Every proxied request to the backend carries this header
DEVICE_HEADER = {"X-Sahayak-Device": "raspberry-pi"}

# ──────────────────────────────────────────────────────────────────────────────
# Camera — OpenCV face recognition HUD (optional)
#
# Default: ENABLE_FACE_HUD=false in config.env
#   → camera stays free for the browser to use via getUserMedia (document scanning)
#
# Set ENABLE_FACE_HUD=true only if you have a SECOND camera dedicated to face
# recognition. Running OpenCV on the same camera as the browser will block
# document scanning in the React UI.
# ──────────────────────────────────────────────────────────────────────────────
camera_thread = None

if config.ENABLE_FACE_HUD:
    try:
        from face_service import FaceService, CameraStreamThread
        _face_svc = FaceService(models_dir=config.MODELS_DIR, db_path=config.DB_PATH)
        camera_thread = CameraStreamThread(
            camera_id=config.CAMERA_INDEX, face_service=_face_svc
        )
        logger.info("Face recognition HUD enabled on camera %d", config.CAMERA_INDEX)
    except Exception as exc:
        logger.warning("Face HUD disabled — could not load face_service: %s", exc)
else:
    logger.info("Face HUD disabled (ENABLE_FACE_HUD=false) — camera free for browser")


# ══════════════════════════════════════════════════════════════════════════════
# React SPA — serve the built frontend
#
# Vite outputs:
#   static/index.html          — entry point
#   static/assets/*.js / *.css — hashed bundles
#
# All real files are served directly.
# Everything else falls through to index.html so React Router works.
# /api/* routes below are matched first by Flask before this catch-all.
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path: str):
    if path:
        target = STATIC_DIR / path
        if target.exists() and target.is_file():
            return send_from_directory(str(STATIC_DIR), path)

    index = STATIC_DIR / "index.html"
    if not index.exists():
        return (
            "<h1>Kiosk UI not built</h1>"
            "<p>Run <code>cd frontend &amp;&amp; npm run build:kiosk</code> "
            "on your dev machine, then copy <code>physical_kiosk_raspberrypi/static/</code> "
            "to the Pi.</p>",
            503,
        )
    return send_from_directory(str(STATIC_DIR), "index.html")


# ══════════════════════════════════════════════════════════════════════════════
# Backend Proxy — /api/* → central FastAPI backend + X-Sahayak-Device: raspberrypi
#
# The React app calls /api/* on the same origin (this Flask server, port 5000).
# Flask forwards everything to BACKEND_SERVER_URL, always adding the device header.
# The backend URL and all secrets never appear in the browser.
# ══════════════════════════════════════════════════════════════════════════════

def _backend_url(path: str) -> str:
    return f"{config.BACKEND_SERVER_URL.rstrip('/')}{path}"


def _forward(method: str, path: str, **kwargs) -> Response:
    """Forward a request to the backend and relay the response verbatim."""
    extra_headers = kwargs.pop("extra_headers", {})
    timeout = kwargs.pop("timeout", 20)
    try:
        res = requests.request(
            method,
            _backend_url(path),
            headers={**DEVICE_HEADER, **extra_headers},
            timeout=timeout,
            **kwargs,
        )
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except requests.exceptions.ConnectionError:
        logger.warning("Backend unreachable: %s %s", method, path)
        return jsonify({"detail": "Backend server is unreachable"}), 503
    except Exception as exc:
        logger.error("Proxy error %s %s: %s", method, path, exc)
        return jsonify({"detail": str(exc)}), 503


# ── LiveKit token ─────────────────────────────────────────────────────────────
@app.route("/api/token")
def proxy_token():
    params = {**request.args, "client_device": "raspberry-pi"}
    return _forward("GET", "/api/token", params=params)


# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def proxy_health():
    return _forward("GET", "/api/health", timeout=5)


# ── Auth / WebAuthn ───────────────────────────────────────────────────────────
@app.route("/api/auth/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy_auth(subpath: str):
    return _forward(
        request.method, f"/api/auth/{subpath}",
        params=request.args,
        json=request.get_json(silent=True),
    )


# ── Guest sessions ────────────────────────────────────────────────────────────
@app.route("/api/guest-sessions", methods=["POST"])
def proxy_guest_sessions_create():
    return _forward("POST", "/api/guest-sessions")


@app.route("/api/guest-sessions/<session_id>", methods=["DELETE"])
def proxy_guest_sessions_delete(session_id: str):
    return _forward("DELETE", f"/api/guest-sessions/{session_id}")


# ── Chat + document upload ────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def proxy_chat():
    files = {}
    if "document" in request.files:
        f = request.files["document"]
        files["document"] = (f.filename, f.stream, f.content_type)
    return _forward(
        "POST", "/api/chat",
        data=request.form.to_dict(),
        files=files or None,
        timeout=30,
    )


# ── Profile ───────────────────────────────────────────────────────────────────
@app.route("/api/profile", methods=["GET", "PUT"])
def proxy_profile():
    if request.method == "GET":
        return _forward("GET", "/api/profile", params=request.args)
    return _forward(
        "PUT", "/api/profile",
        json=request.get_json(silent=True),
        extra_headers={"Content-Type": "application/json"},
    )


# ── Schemes ───────────────────────────────────────────────────────────────────
@app.route("/api/schemes", methods=["GET"])
def proxy_schemes():
    return _forward("GET", "/api/schemes", params=request.args, timeout=12)


@app.route("/api/schemes/filters", methods=["GET"])
def proxy_scheme_filters():
    return _forward("GET", "/api/schemes/filters", params=request.args)


@app.route("/api/schemes/<slug>", methods=["GET"])
def proxy_scheme_detail(slug: str):
    return _forward("GET", f"/api/schemes/{slug}")


# ── Grievances ────────────────────────────────────────────────────────────────
@app.route("/api/grievances", methods=["GET", "POST"])
def proxy_grievances():
    if request.method == "GET":
        return _forward("GET", "/api/grievances", params=request.args)
    return _forward(
        "POST", "/api/grievances",
        json=request.get_json(silent=True),
        extra_headers={"Content-Type": "application/json"},
    )


@app.route("/api/grievances/<grievance_id>", methods=["GET", "PUT", "DELETE"])
def proxy_grievance_detail(grievance_id: str):
    return _forward(
        request.method, f"/api/grievances/{grievance_id}",
        json=request.get_json(silent=True),
    )


# ── Knowledge Base ────────────────────────────────────────────────────────────
@app.route("/api/knowledge-base/upload", methods=["POST"])
def proxy_kb_upload():
    files = {}
    if "file" in request.files:
        f = request.files["file"]
        files["file"] = (f.filename, f.stream, f.content_type)
    return _forward(
        "POST", "/api/knowledge-base/upload",
        data=request.form.to_dict(),
        files=files or None,
        timeout=60,
    )


@app.route("/api/knowledge-base/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_kb(subpath: str):
    return _forward(
        request.method, f"/api/knowledge-base/{subpath}",
        params=request.args,
        json=request.get_json(silent=True),
    )


# ── Admin ─────────────────────────────────────────────────────────────────────
@app.route("/api/admin/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_admin(subpath: str):
    return _forward(
        request.method, f"/api/admin/{subpath}",
        params=request.args,
        json=request.get_json(silent=True),
    )


# ── Notifications ─────────────────────────────────────────────────────────────
@app.route("/api/notifications", methods=["GET"])
def proxy_notifications():
    return _forward("GET", "/api/notifications", params=request.args)


@app.route("/api/notifications/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_notifications_sub(subpath: str):
    return _forward(
        request.method, f"/api/notifications/{subpath}",
        params=request.args,
        json=request.get_json(silent=True),
    )


# ── Documents ─────────────────────────────────────────────────────────────────
@app.route("/api/documents", methods=["GET", "POST"])
def proxy_documents():
    if request.method == "GET":
        return _forward("GET", "/api/documents", params=request.args)
    files = {}
    if "file" in request.files:
        f = request.files["file"]
        files["file"] = (f.filename, f.stream, f.content_type)
    return _forward(
        "POST", "/api/documents",
        data=request.form.to_dict(),
        files=files or None,
        timeout=30,
    )


@app.route("/api/documents/<path:subpath>", methods=["GET", "PUT", "DELETE"])
def proxy_documents_sub(subpath: str):
    return _forward(
        request.method, f"/api/documents/{subpath}",
        params=request.args,
        json=request.get_json(silent=True),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Hardware status + optional camera MJPEG feed
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/hardware_status")
def hardware_status():
    """Kiosk device + backend connectivity status for the UI status bar."""
    backend_ok = False
    try:
        res = requests.get(_backend_url("/api/health"), headers=DEVICE_HEADER, timeout=3)
        backend_ok = res.status_code == 200
    except Exception:
        pass

    return jsonify({
        "device": "raspberrypi",
        "backend_connected": backend_ok,
        "backend_url": config.BACKEND_SERVER_URL,
        "face_hud_active": camera_thread is not None and camera_thread.is_running,
    })


@app.route("/video_feed")
def video_feed():
    """MJPEG stream of the OpenCV face recognition HUD (only when ENABLE_FACE_HUD=true)."""
    if camera_thread is None:
        return jsonify({"detail": "Face HUD not enabled (ENABLE_FACE_HUD=false)"}), 404

    def frames():
        while True:
            frame = camera_thread.get_mjpeg_frame()
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(0.033)

    return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    logger.info("=" * 58)
    logger.info("  Sahayak AI — Raspberry Pi Physical Kiosk Server")
    logger.info("=" * 58)
    logger.info("  Backend  : %s", config.BACKEND_SERVER_URL)
    logger.info("  Agent    : %s", config.AGENT_NAME)
    logger.info("  Port     : %s", config.PORT)
    logger.info("  UI dir   : %s", STATIC_DIR)
    logger.info("  Face HUD : %s", "enabled" if camera_thread else "disabled")

    if not (STATIC_DIR / "index.html").exists():
        logger.warning(
            "React build not found in static/ — "
            "run 'cd frontend && npm run build:kiosk' on your dev machine"
        )
    logger.info("=" * 58)

    if camera_thread:
        camera_thread.start()

    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if camera_thread:
            camera_thread.stop()
        logger.info("Goodbye.")


if __name__ == "__main__":
    main()
