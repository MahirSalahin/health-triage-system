"""Report and TTS endpoints — Task 5."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from openai import OpenAI
from sqlmodel import Session

from app.api.deps import get_ai, get_db
from app.core.config import settings
from app.crud.triage_session import get_triage_session
from app.schemas.triage import TriageResult
from app.schemas.vitals import VitalsAnalysisResponse
from app.schemas.document import MedicalEntities
from app.services.report_service import generate_pdf_report, generate_summary
from app.services.tts_service import generate_speech

router = APIRouter(prefix="/reports", tags=["reports"])



@router.get("/{session_id}/pdf")
def get_pdf_report(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generate and download a professional PDF report for a triage session.
    """
    session = get_triage_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Triage session not found")

    if not session.triage_result_json:
        raise HTTPException(
            status_code=400, detail="Triage has not been completed for this session"
        )

    triage_result = TriageResult(**json.loads(session.triage_result_json))

    vitals_analysis = None
    if session.vitals_anomalies_json:
        vitals_analysis = VitalsAnalysisResponse(
            **json.loads(session.vitals_anomalies_json)
        )

    medical_entities = None
    if session.medical_entities_json:
        medical_entities = MedicalEntities(**json.loads(session.medical_entities_json))

    pdf_bytes = generate_pdf_report(
        patient_name=session.patient_name,
        patient_age=session.patient_age,
        patient_sex=session.patient_sex,
        symptoms=session.symptoms_english or session.symptoms_original,
        triage_result=triage_result,
        vitals_analysis=vitals_analysis,
        medical_entities=medical_entities,
        created_at=session.created_at.strftime("%Y-%m-%d %H:%M:%S") if session.created_at else None,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="triage_report_{session_id}.pdf"'
        },
    )


@router.get("/{session_id}/audio-summary")
def get_audio_summary(
    session_id: uuid.UUID,
    language: str = "en",
    client: OpenAI = Depends(get_ai),
    db: Session = Depends(get_db),
):
    """
    Generate an audio spoken summary of the triage result.
    Language can be "en" or "bn".
    """
    session = get_triage_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Triage session not found")

    if not session.triage_result_json:
        raise HTTPException(
            status_code=400, detail="Triage has not been completed for this session"
        )

    triage_result = TriageResult(**json.loads(session.triage_result_json))

    # Generate LLM summary text
    summary_text = generate_summary(
        client=client,
        model=settings.LLM_MODEL,
        triage_result=triage_result,
        patient_name=session.patient_name,
        patient_age=session.patient_age,
    )

    # Translate summary if Bengali requested
    if language == "bn":
        # Using Gemini to translate the summary to Bengali before TTS
        from app.services.speech_service import genai
        
        genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[f"Translate the following triage summary to Bengali cleanly without any markdown or conversational filler:\n\n{summary_text}"],
        )
        summary_text = response.text or summary_text

    # Generate TTS audio
    audio_bytes = generate_speech(text=summary_text, language=language)

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="triage_summary_{session_id}.mp3"'
        },
    )
