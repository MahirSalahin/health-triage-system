"""Document scanning endpoints — Task 2 (OCR + NER)."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from openai import OpenAI

from app.api.deps import get_ai
from app.core.config import settings
from app.schemas.document import DocumentScanResponse
from app.services.ocr_service import scan_document

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


@router.post("/scan", response_model=DocumentScanResponse)
async def scan_medical_document(
    file: UploadFile = File(..., description="Photo of prescription or lab report"),
    client: OpenAI = Depends(get_ai),
):
    """
    Upload a photo of a prescription or lab report.

    The system will:
    1. Extract all text from the image (OCR via AI vision).
    2. Identify and structure medical entities (medications, diagnoses,
       lab tests, allergies) from the extracted text.
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
            f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    # Validate file size
    image_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB} MB",
        )

    result = scan_document(
        client=client,
        model=settings.VISION_MODEL,
        image_bytes=image_bytes,
        mime_type=file.content_type,
    )

    return result
