"""
Multilingual speech-to-text + translation — Task 1.

Uses google-genai SDK for audio transcription since Gemini's OpenAI-compat
endpoint does NOT support client.audio.transcriptions.create().

Migration to OpenAI:
    Replace the transcribe_audio() body with:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    Then translate via chat completion if needed.
"""

import json
import logging

from google import genai
from google.genai import types

from app.utils.prompts import TRANSCRIPTION_PROMPT

logger = logging.getLogger(__name__)


def transcribe_audio(
    api_key: str,
    audio_bytes: bytes,
    mime_type: str,
) -> dict:
    """
    Transcribe audio (Bengali or English) and translate to English.

    Uses Gemini's native multimodal API via google-genai SDK — this is
    the ONE service that isn't OpenAI SDK compatible (because Gemini's
    OpenAI-compat layer doesn't expose audio transcription).

    Args:
        api_key: Gemini API key.
        audio_bytes: Raw audio file bytes.
        mime_type: Audio MIME type (e.g. "audio/wav", "audio/webm").

    Returns:
        dict with keys: original_text, english_text, detected_language
    """
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            TRANSCRIPTION_PROMPT,
        ],
    )

    raw_text = response.text or "{}"

    # Strip markdown code fences if present (Gemini sometimes wraps JSON)
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove ```json or ``` prefix and ``` suffix
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        result = json.loads(cleaned)
        return {
            "original_text": result.get("original_text", ""),
            "english_text": result.get("english_text", ""),
            "detected_language": result.get("detected_language", "en"),
        }
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(
            f"Failed to parse transcription JSON: {e}. Raw: {raw_text}"
        )
        # Fallback: treat raw response as English text
        return {
            "original_text": raw_text,
            "english_text": raw_text,
            "detected_language": "en",
        }


def translate_text(
    api_key: str,
    text: str,
    source_language: str = "auto",
) -> dict:
    """
    Translate text (Bengali or English) and detect language.

    Used for text-based symptom intake as a fallback when voice is not used.

    Args:
        api_key: Gemini API key.
        text: Input text in Bengali or English.
        source_language: "auto", "en", or "bn".

    Returns:
        dict with keys: original_text, english_text, detected_language
    """
    client = genai.Client(api_key=api_key)

    prompt = (
        f"The following text is a patient's symptom description. "
        f"Detect the language and translate to English if needed.\n\n"
        f"Text: {text}\n\n"
        f"Return JSON: {{"
        f'"original_text": "the input text as-is", '
        f'"english_text": "English translation (same if already English)", '
        f'"detected_language": "en" or "bn"'
        f"}}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
    )

    raw_text = response.text or "{}"

    # Strip markdown code fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        result = json.loads(cleaned)
        return {
            "original_text": result.get("original_text", text),
            "english_text": result.get("english_text", text),
            "detected_language": result.get("detected_language", "en"),
        }
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(
            f"Failed to parse translation JSON: {e}. Raw: {raw_text}"
        )
        return {
            "original_text": text,
            "english_text": text,
            "detected_language": source_language if source_language != "auto" else "en",
        }
