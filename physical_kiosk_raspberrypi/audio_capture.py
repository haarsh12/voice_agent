# Hybrid Audio Capturer for Raspberry Pi Kiosk Hardware
# Supports ALSA Input (USB Mic / I2S INMP441) with Automatic VAD and Push-to-Talk

import subprocess
import threading
import time
import logging
import numpy as np
import config

logger = logging.getLogger("SahayakAudio")

class HybridAudioCapturer:
    def __init__(self, callback, alsa_device=config.ALSA_RECORD_DEVICE, sample_rate=config.SAMPLE_RATE, channels=config.CHANNELS, bit_depth=config.BIT_DEPTH):
        self.callback = callback
        self.alsa_device = alsa_device
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth
        
        self.is_running = False
        self.is_button_recording = False
        self.button_audio_chunks = []
        self.current_volume = 0.0
        
        self.process = None
        self.thread = None
        self._lock = threading.Lock()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started Audio Capturer on ALSA device '{self.alsa_device}'")

    def stop(self):
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

    def start_button_recording(self):
        with self._lock:
            self.button_audio_chunks = []
            self.is_button_recording = True
        logger.info("🔴 UI Button Recording STARTED...")

    def stop_button_recording(self) -> bytes:
        with self._lock:
            self.is_button_recording = False
            chunks = list(self.button_audio_chunks)
            self.button_audio_chunks = []

        logger.info(f"⬛ UI Button Recording STOPPED. Total chunks: {len(chunks)}")
        if not chunks:
            return b""

        raw_bytes = b"".join(chunks)
        pcm16_bytes, _ = self._process_audio_chunk(raw_bytes)
        return pcm16_bytes

    def _process_audio_chunk(self, raw_bytes: bytes) -> tuple[bytes, float]:
        if not raw_bytes:
            return b"", 0.0

        try:
            bytes_per_sample = 4 if "S32" in self.bit_depth else 2
            bytes_per_frame = self.channels * bytes_per_sample
            remainder = len(raw_bytes) % bytes_per_frame
            if remainder > 0:
                raw_bytes = raw_bytes[:-remainder]

            if not raw_bytes:
                return b"", 0.0

            if "S32" in self.bit_depth:
                audio_raw = np.frombuffer(raw_bytes, dtype=np.int32)
                if self.channels > 1:
                    raw_matrix = audio_raw.reshape(-1, self.channels)
                    ch0, ch1 = raw_matrix[:, 0], raw_matrix[:, 1]
                    rms0 = np.sqrt(np.mean((ch0 >> 8).astype(np.float32) ** 2)) if len(ch0) > 0 else 0
                    rms1 = np.sqrt(np.mean((ch1 >> 8).astype(np.float32) ** 2)) if len(ch1) > 0 else 0
                    audio_raw = ch0 if rms0 >= rms1 else ch1
                audio_float = (audio_raw >> 8).astype(np.float32) / 8388608.0
            else:
                audio_raw = np.frombuffer(raw_bytes, dtype=np.int16)
                if self.channels > 1:
                    raw_matrix = audio_raw.reshape(-1, self.channels)
                    ch0, ch1 = raw_matrix[:, 0], raw_matrix[:, 1]
                    rms0 = np.sqrt(np.mean(ch0.astype(np.float32) ** 2)) if len(ch0) > 0 else 0
                    rms1 = np.sqrt(np.mean(ch1.astype(np.float32) ** 2)) if len(ch1) > 0 else 0
                    audio_raw = ch0 if rms0 >= rms1 else ch1
                audio_float = audio_raw.astype(np.float32) / 32768.0

            if self.sample_rate == 48000:
                n = (len(audio_float) // 3) * 3
                if n > 0:
                    audio_float = (audio_float[0:n:3] + audio_float[1:n:3] + audio_float[2:n:3]) / 3.0

            rms = float(np.sqrt(np.mean(audio_float ** 2))) if len(audio_float) > 0 else 0.0

            if rms > 0.0001:
                target_rms = 0.15
                gain = min(target_rms / (rms + 1e-6), 4.0)
                audio_float = audio_float * gain

            audio_pcm16 = (np.clip(audio_float, -1.0, 1.0) * 32767.0).astype(np.int16)
            return audio_pcm16.tobytes(), rms
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return b"", 0.0

    def _capture_loop(self):
        cmd = [
            "arecord",
            "-D", self.alsa_device,
            "-f", self.bit_depth,
            "-r", str(self.sample_rate),
            "-c", str(self.channels),
            "-t", "raw"
        ]

        logger.info(f"Launching ALSA capture command: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=4096 * 8
            )
        except Exception as e:
            logger.error(f"Could not start arecord process: {e}")
            return

        bytes_per_sample = 4 if "S32" in self.bit_depth else 2
        bytes_per_chunk = int(self.sample_rate * bytes_per_sample * self.channels * 0.1)

        pcm_accumulator = bytearray()
        silent_chunks = 0
        speaking = False

        while self.is_running:
            raw_data = self.process.stdout.read(bytes_per_chunk)
            if not raw_data:
                time.sleep(0.05)
                continue

            pcm16_chunk, rms = self._process_audio_chunk(raw_data)
            self.current_volume = rms

            with self._lock:
                if self.is_button_recording:
                    self.button_audio_chunks.append(raw_data)

            if rms > 0.005:
                if not speaking:
                    speaking = True
                pcm_accumulator.extend(pcm16_chunk)
                silent_chunks = 0
            elif speaking:
                pcm_accumulator.extend(pcm16_chunk)
                silent_chunks += 1
                if silent_chunks >= 6:  # ~0.6s silence threshold
                    if not self.is_button_recording and len(pcm_accumulator) >= int(16000 * 2 * 0.6):
                        self.callback(bytes(pcm_accumulator), rms)
                    pcm_accumulator.clear()
                    speaking = False
                    silent_chunks = 0
