"""
Text-to-speech service — Task 5 (audio summary).

Uses gTTS (Google Text-to-Speech) for both Bengali and English.
Free, no API key needed, supports Bengali out of the box.

Migration to OpenAI:
    Replace generate_speech() body with:
        response = client.audio.speech.create(
            model="tts-1", voice="alloy", input=text
        )
        return response.content
"""

import io
import logging

from gtts import gTTS

logger = logging.getLogger(__name__)


def generate_speech(text: str, language: str = "en") -> bytes:
    """
    Generate speech audio from text.

    Args:
        text: Text to convert to speech.
        language: "en" for English, "bn" for Bengali.

    Returns:
        MP3 audio bytes.
    """
    lang_code = "bn" if language == "bn" else "en"

    try:
        tts = gTTS(text=text, lang=lang_code)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise
