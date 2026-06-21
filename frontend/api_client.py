import os
import requests
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Use the backend API URL from env, or default to localhost
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api")

class TriageAPIClient:
    """Client for interacting with the FastAPI backend."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=5)
            return res.status_code == 200
        except Exception:
            return False

    def text_intake(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """Submit symptom text for translation/processing."""
        res = requests.post(
            f"{self.base_url}/intake/text",
            json={"text": text, "language": language},
            timeout=15
        )
        res.raise_for_status()
        return res.json()

    def voice_intake(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> Dict[str, Any]:
        """Submit voice audio for transcription/translation."""
        files = {
            "file": ("audio.wav", audio_bytes, mime_type)
        }
        res = requests.post(
            f"{self.base_url}/intake/voice",
            files=files,
            timeout=30
        )
        res.raise_for_status()
        return res.json()

    def scan_document(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Upload a medical document image for OCR and NER."""
        files = {
            "file": ("document.jpg", image_bytes, mime_type)
        }
        res = requests.post(
            f"{self.base_url}/documents/scan",
            files=files,
            timeout=45
        )
        res.raise_for_status()
        return res.json()

    def analyze_vitals(self, vitals_data: dict, patient_age: int) -> Dict[str, Any]:
        """Check vitals for anomalies."""
        res = requests.post(
            f"{self.base_url}/vitals/analyze",
            params={"patient_age": patient_age},
            json=vitals_data,
            timeout=10
        )
        res.raise_for_status()
        return res.json()

    def run_triage(self, triage_request: dict) -> Dict[str, Any]:
        """Run the full AI triage reasoning."""
        res = requests.post(
            f"{self.base_url}/triage/analyze",
            json=triage_request,
            timeout=45
        )
        res.raise_for_status()
        return res.json()

    def download_pdf_report(self, session_id: str) -> bytes:
        """Download the PDF report from the backend."""
        res = requests.get(f"{self.base_url}/reports/{session_id}/pdf", timeout=15)
        res.raise_for_status()
        return res.content

    def download_audio_summary(self, session_id: str, language: str = "en") -> bytes:
        """Download the TTS audio summary from the backend."""
        res = requests.get(
            f"{self.base_url}/reports/{session_id}/audio-summary",
            params={"language": language},
            timeout=100
        )
        res.raise_for_status()
        return res.content

api = TriageAPIClient()
