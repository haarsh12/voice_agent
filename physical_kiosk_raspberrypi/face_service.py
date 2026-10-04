# High-Performance OpenCV Face Detection & Recognition Service
# Real-time Mobile FaceID HUD visualization and low-latency camera stream thread

import os
import sqlite3
import numpy as np
import cv2
import logging
import threading
import time
import config

logger = logging.getLogger("SahayakFace")

def draw_facelock_ui(frame, bbox, label, color=(0, 255, 0), progress=1.0, is_unlocked=True):
    """
    Renders sleek Kiosk FaceID target HUD overlay with corner brackets,
    scanning progress indicator, and translucent badge.
    """
    x, y, w, h = bbox
    l = max(15, min(w, h) // 4)
    t = 2

    # Corner Brackets ( Top-Left, Top-Right, Bottom-Left, Bottom-Right )
    cv2.line(frame, (x, y), (x + l, y), color, t)
    cv2.line(frame, (x, y), (x, y + l), color, t)
    cv2.line(frame, (x + w, y), (x + w - l, y), color, t)
    cv2.line(frame, (x + w, y), (x + w, y + l), color, t)
    cv2.line(frame, (x, y + h), (x + l, y + h), color, t)
    cv2.line(frame, (x, y + h), (x, y + h - l), color, t)
    cv2.line(frame, (x + w, y + h), (x + w - l, y + h), color, t)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - l), color, t)

    # Progress Bar during scanning
    if not is_unlocked:
        bar_w = int(w * progress)
        cv2.rectangle(frame, (x, y + h + 8), (x + w, y + h + 14), (40, 40, 40), -1)
        cv2.rectangle(frame, (x, y + h + 8), (x + bar_w, y + h + 14), (0, 215, 255), -1)

    # Translucent Label Badge
    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    badge_w = text_size[0] + 20
    badge_h = 26
    badge_x = max(10, x + (w - badge_w) // 2)
    badge_y = y - 10 if y - 35 > 10 else y + h + 30

    y1, y2 = max(0, badge_y - badge_h), min(frame.shape[0], badge_y)
    x1, x2 = max(0, badge_x), min(frame.shape[1], badge_x + badge_w)

    if (y2 - y1) > 0 and (x2 - x1) > 0:
        sub = frame[y1:y2, x1:x2]
        black_bg = np.full(sub.shape, (15, 23, 42), dtype=np.uint8)
        frame[y1:y2, x1:x2] = cv2.addWeighted(sub, 0.3, black_bg, 0.7, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
        cv2.putText(frame, label, (x1 + 10, y2 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

class FaceService:
    def __init__(self, models_dir=config.MODELS_DIR, db_path=config.DB_PATH):
        self.models_dir = os.path.abspath(models_dir)
        self.db_path = os.path.abspath(db_path)
        
        self.yunet_path = os.path.join(self.models_dir, "yunet.onnx")
        self.sface_path = os.path.join(self.models_dir, "sface.onnx")
        
        self.detector = None
        self.recognizer = None
        self.similarity_threshold = 0.363
        
        self._init_db()
        self._init_models()
        self.known_embeddings = []
        self.load_known_embeddings()
        self.pending_scans = {}

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()
        conn.close()

    def _init_models(self):
        os.makedirs(self.models_dir, exist_ok=True)
        import urllib.request

        yunet_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
        sface_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

        if not os.path.exists(self.yunet_path):
            logger.info("Downloading YuNet face detection model (yunet.onnx)...")
            try:
                urllib.request.urlretrieve(yunet_url, self.yunet_path)
            except Exception as e:
                logger.error(f"Failed to download YuNet model: {e}")

        if not os.path.exists(self.sface_path):
            logger.info("Downloading SFace face recognition model (sface.onnx)...")
            try:
                urllib.request.urlretrieve(sface_url, self.sface_path)
            except Exception as e:
                logger.error(f"Failed to download SFace model: {e}")

        if not os.path.exists(self.yunet_path) or not os.path.exists(self.sface_path):
            logger.warning(f"YuNet or SFace models missing at '{self.models_dir}'.")
            return

        try:
            self.detector = cv2.FaceDetectorYN.create(
                model=self.yunet_path,
                config="",
                input_size=(640, 480),
                score_threshold=0.75,
                nms_threshold=0.3
            )
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=self.sface_path,
                config=""
            )
            logger.info("Loaded YuNet & SFace models successfully.")
        except Exception as e:
            logger.error(f"Failed to load OpenCV face models: {e}")

    def load_known_embeddings(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, embedding FROM embeddings")
        rows = cursor.fetchall()
        conn.close()

        self.known_embeddings = []
        for user_id, emb_blob in rows:
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            self.known_embeddings.append((user_id, emb))
        logger.info(f"Loaded {len(self.known_embeddings)} face embeddings from database.")

    def save_new_user_multi(self, embeddings_list) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
        count = cursor.fetchone()[0] + 1
        user_id = f"USER_{count:03d}"
        
        cursor.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, f"Person {count}"))
        for emb in embeddings_list:
            cursor.execute("INSERT INTO embeddings (user_id, embedding) VALUES (?, ?)", (user_id, emb.astype(np.float32).tobytes()))
            self.known_embeddings.append((user_id, emb.astype(np.float32)))
            
        conn.commit()
        conn.close()
        logger.info(f"👤 Registered NEW USER '{user_id}' with {len(embeddings_list)} face samples in SQLite!")
        return user_id

    def process_frame(self, frame):
        if self.detector is None or self.recognizer is None or frame is None:
            return frame, []

        h, w = frame.shape[:2]
        self.detector.setInputSize((w, h))

        _, faces = self.detector.detect(frame)
        detected_users = []
        current_scans = {}

        if faces is not None:
            for face in faces:
                bbox = list(map(int, face[0:4]))
                x, y, box_w, box_h = bbox
                
                if box_w < 50 or box_h < 50:
                    continue

                aligned_face = self.recognizer.alignCrop(frame, face)
                feature = self.recognizer.feature(aligned_face)

                best_match_id = None
                best_score = -1.0

                feature_2d = feature.reshape(1, -1).astype(np.float32)
                for user_id, saved_emb in self.known_embeddings:
                    try:
                        saved_emb_2d = saved_emb.reshape(1, -1).astype(np.float32)
                        score = self.recognizer.match(feature_2d, saved_emb_2d, cv2.FaceRecognizerSF_FR_COSINE)
                        if score > best_score:
                            best_score = score
                            best_match_id = user_id
                    except Exception:
                        pass

                if best_score >= self.similarity_threshold and best_match_id:
                    matched_id = best_match_id
                    label = f"FACE UNLOCKED: {matched_id}"
                    draw_facelock_ui(frame, [x, y, box_w, box_h], label, color=(0, 255, 0), progress=1.0, is_unlocked=True)
                    detected_users.append({"user_id": matched_id, "bbox": [x, y, box_w, box_h], "confidence": float(best_score)})
                else:
                    track_key = f"{x // 40}_{y // 40}"
                    scanned_samples = self.pending_scans.get(track_key, [])
                    scanned_samples.append(feature[0])
                    current_scans[track_key] = scanned_samples

                    scan_count = len(scanned_samples)
                    progress = min(1.0, scan_count / 3.0)

                    if scan_count < 3:
                        label = f"SCANNING STRUCTURE ({int(progress * 100)}%)..."
                        draw_facelock_ui(frame, [x, y, box_w, box_h], label, color=(0, 215, 255), progress=progress, is_unlocked=False)
                    else:
                        new_id = self.save_new_user_multi(scanned_samples)
                        label = f"FACE REGISTERED: {new_id}"
                        draw_facelock_ui(frame, [x, y, box_w, box_h], label, color=(0, 255, 0), progress=1.0, is_unlocked=True)
                        detected_users.append({"user_id": new_id, "bbox": [x, y, box_w, box_h], "confidence": 1.0})

        self.pending_scans = current_scans
        return frame, detected_users

class CameraStreamThread:
    def __init__(self, camera_id=config.CAMERA_INDEX, face_service=None):
        self.camera_id = camera_id
        self.face_service = face_service
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.processed_frame = None
        self._lock = threading.Lock()
        self.thread = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

    def _update_loop(self):
        cam_indices = [self.camera_id, 0, 1, 2, 4]
        opened = False

        for idx in cam_indices:
            for backend in [cv2.CAP_V4L2, cv2.CAP_ANY]:
                try:
                    self.cap = cv2.VideoCapture(idx, backend)
                    if self.cap and self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
                        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
                        time.sleep(0.05)
                        
                        for _ in range(3):
                            ret, test_frame = self.cap.read()
                            if ret and test_frame is not None:
                                logger.info(f"Connected to webcam on device index /dev/video{idx}")
                                opened = True
                                break
                            time.sleep(0.03)

                        if opened:
                            break
                        else:
                            self.cap.release()
                except Exception:
                    pass
            if opened:
                break

        if not opened:
            logger.error("Could not open USB camera on any video index.")
            return

        last_face_time = 0

        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                with self._lock:
                    self.current_frame = frame

                now = time.time()
                if self.face_service and (now - last_face_time >= 0.08):
                    last_face_time = now
                    try:
                        annotated_frame, _ = self.face_service.process_frame(frame.copy())
                        with self._lock:
                            self.processed_frame = annotated_frame
                    except Exception as fe:
                        logger.error(f"Error processing face frame: {fe}")
                elif self.processed_frame is None:
                    with self._lock:
                        self.processed_frame = frame.copy()
            except Exception as e:
                logger.error(f"Error in camera capture loop: {e}")
                time.sleep(0.05)

    def get_mjpeg_frame(self):
        with self._lock:
            frame = self.processed_frame if self.processed_frame is not None else self.current_frame

        if frame is None:
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "Initializing Camera Stream...", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            _, jpeg = cv2.imencode('.jpg', blank)
            return jpeg.tobytes()

        _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        return jpeg.tobytes()
