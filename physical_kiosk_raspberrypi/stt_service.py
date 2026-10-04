# STT Service for Sahayak AI Kiosk

import os
import sys
import logging
import re
from google.oauth2 import service_account
from google.cloud import speech

logger = logging.getLogger("SahayakSTT")

def normalize_scheme_terms(text: str) -> str:
    """
    Normalizes common STT phonetic misrecognitions for government scheme terms.
    """
    if not text:
        return ""
    text = re.sub(r'\b(pmsby|pms bi y|pmf bi y|pm f b y|p m f b y|pmfbyy|pmsb|pms)\b', 'PMFBY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(pm kisan|p m kisan|pmkisan)\b', 'PM-KISAN', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(kcc|kisan credit card)\b', 'KCC', text, flags=re.IGNORECASE)
    return text

class STTService:
    def __init__(self, sample_rate=16000, language_code=None):
        self.sample_rate = sample_rate
        self.language_code = language_code or os.environ.get("STT_LANGUAGE", "en-IN")
        self.client = None
        self._init_client()

    def _init_client(self):
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path or not os.path.exists(creds_path):
            logger.warning(f"Google Application Credentials not found at '{creds_path}'.")
            return

        try:
            creds = service_account.Credentials.from_service_account_file(creds_path)
            self.client = speech.SpeechClient(credentials=creds)
            logger.info(f"Connected to Google Cloud Speech API ({self.language_code}).")
        except Exception as e:
            logger.error(f"Failed to connect to Google Cloud Speech API: {e}")

    def transcribe_pcm16_chunk(self, pcm_data: bytes) -> str:
        """
        Transcribes 16kHz 16-bit PCM audio chunk via Google Cloud Speech-to-Text.
        """
        if not pcm_data or len(pcm_data) == 0:
            return ""

        if not self.client:
            self._init_client()
            if not self.client:
                return "[Error: Google Speech Client unavailable]"

        duration_sec = len(pcm_data) / (self.sample_rate * 2)
        audio = speech.RecognitionAudio(content=pcm_data)
        
        scheme_keywords = [
            "PMFBY", "P M F B Y", "Pradhan Mantri Fasal Bima Yojana", "Fasal Bima",
            "PMSBY", "Pradhan Mantri Suraksha Bima Yojana",
            "PM-KISAN", "PM Kisan", "Sahayak", "Sahayak AI",
            "Aadhaar", "Yojana", "Kisan", "Ration Card", "DBT", "Crop Insurance",
            "Kisan Credit Card", "KCC", "Ayushman Bharat", "E-Shram"
        ]
        speech_context = speech.SpeechContext(phrases=scheme_keywords, boost=30.0)
        supported_langs = ["hi-IN", "en-IN", "mr-IN", "gu-IN", "ta-IN", "te-IN", "kn-IN", "bn-IN"]
        alt_langs = [l for l in supported_langs if l != self.language_code][:3]

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate,
            language_code=self.language_code,
            alternative_language_codes=alt_langs,
            speech_contexts=[speech_context],
            enable_automatic_punctuation=True,
            use_enhanced=True
        )

        try:
            response = self.client.recognize(config=config, audio=audio)
            transcript_parts = [
                result.alternatives[0].transcript 
                for result in response.results if result.alternatives
            ]
            full_transcript = normalize_scheme_terms(" ".join(transcript_parts).strip())
            if full_transcript:
                logger.info(f"Recognized ({duration_sec:.1f}s): '{full_transcript}'")
            return full_transcript
        except Exception as e:
            logger.error(f"Google STT API Exception: {e}")
            return f"[STT Error: {str(e)}]"
