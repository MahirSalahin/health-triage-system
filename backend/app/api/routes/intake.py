"""Patient intake endpoints — Task 1 (Voice + Text)."""

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.schemas.intake import TextIntakeRequest, IntakeResponse
from app.services.speech_service import transcribe_audio, translate_text

router = APIRouter(prefix="/intake", tags=["intake"])

ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
}


@router.post("/voice", response_model=IntakeResponse)
async def voice_intake(
    file: UploadFile = File(
        ..., description="Audio recording of patient symptoms (Bengali or English)"
    ),
):
    """
    Upload an audio recording of a patient describing their symptoms.

    The system will:
    1. Transcribe the audio (supports Bengali and English).
    2. Detect the language.
    3. Translate to English if the input is in Bengali.

    The CHW can review and edit the transcription before proceeding.
    """
    # Validate audio type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {content_type}. "
            f"Allowed: {', '.join(ALLOWED_AUDIO_TYPES)}",
        )

    audio_bytes = await file.read()

    # Validate size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB} MB",
        )

    result = transcribe_audio(
        api_key=settings.GEMINI_API_KEY,
        audio_bytes=audio_bytes,
        mime_type=content_type,
    )

    return IntakeResponse(**result)


@router.post("/text", response_model=IntakeResponse)
def text_intake(request: TextIntakeRequest):
    """
    Submit patient symptoms as text (Bengali or English).

    Fallback for when voice input is not available. The system will
    detect the language and translate to English if needed.
    """
    result = translate_text(
        api_key=settings.GEMINI_API_KEY,
        text=request.text,
        source_language=request.language,
    )

    return IntakeResponse(**result)
