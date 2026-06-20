"""
OCR + Named Entity Recognition for medical documents — Task 2.

Uses OpenAI SDK vision (chat completions with image input) for OCR,
then a second LLM call for structured medical entity extraction.

Works on both Gemini (via OpenAI-compat endpoint) and real OpenAI.
"""

import base64
import json
import logging

from openai import OpenAI

from app.schemas.document import DocumentScanResponse, MedicalEntities
from app.utils.prompts import OCR_EXTRACTION_PROMPT, MEDICAL_NER_PROMPT

logger = logging.getLogger(__name__)


def extract_text_from_image(
    client: OpenAI,
    model: str,
    image_bytes: bytes,
    mime_type: str,
) -> str:
    """
    Extract text from a medical document image using LLM vision.

    Args:
        client: OpenAI client (pointed at Gemini or OpenAI).
        model: Vision model name (e.g. "gemini-2.5-flash" or "gpt-4o").
        image_bytes: Raw image bytes.
        mime_type: Image MIME type (e.g. "image/jpeg").

    Returns:
        Raw extracted text from the document.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": OCR_EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_image}"
                        },
                    },
                ],
            }
        ],
    )

    return response.choices[0].message.content or ""


def extract_medical_entities(
    client: OpenAI,
    model: str,
    raw_text: str,
) -> MedicalEntities:
    """
    Extract structured medical entities (medications, diagnoses, lab tests,
    allergies) from raw OCR text using an LLM.

    Args:
        client: OpenAI client.
        model: LLM model name.
        raw_text: Raw text extracted from the medical document.

    Returns:
        Structured MedicalEntities parsed from the text.
    """
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": MEDICAL_NER_PROMPT},
            {
                "role": "user",
                "content": f"Extract medical entities from this text:\n\n{raw_text}",
            },
        ],
    )

    raw_json = response.choices[0].message.content or "{}"

    try:
        parsed = json.loads(raw_json)
        return MedicalEntities(**parsed)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Failed to parse NER response: {e}. Raw: {raw_json}")
        return MedicalEntities()


def scan_document(
    client: OpenAI,
    model: str,
    image_bytes: bytes,
    mime_type: str,
) -> DocumentScanResponse:
    """
    Full document scan pipeline: OCR → NER.

    Args:
        client: OpenAI client.
        model: Vision-capable model name.
        image_bytes: Raw image bytes.
        mime_type: Image MIME type.

    Returns:
        DocumentScanResponse with raw text and structured entities.
    """
    # Step 1: OCR — extract raw text from image
    raw_text = extract_text_from_image(client, model, image_bytes, mime_type)

    # Step 2: NER — extract structured medical entities from text
    entities = extract_medical_entities(client, model, raw_text)

    return DocumentScanResponse(raw_text=raw_text, entities=entities)
