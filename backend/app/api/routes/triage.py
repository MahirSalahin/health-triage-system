"""Triage analysis endpoints — Task 3."""

from fastapi import APIRouter, Depends

from openai import OpenAI
from sqlmodel import Session

from app.api.deps import get_ai, get_db
from app.core.config import settings
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.triage_service import run_triage
from app.services.vitals_service import analyze_vitals
from app.crud.triage_session import create_triage_session

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("/analyze", response_model=TriageResponse)
def analyze_triage(
    request: TriageRequest,
    client: OpenAI = Depends(get_ai),
    db: Session = Depends(get_db),
):
    """
    Run full AI triage analysis.

    Accepts patient info, symptoms, optional medical history, and optional vitals.
    Returns triage score (GREEN/YELLOW/RED/BLACK), reasoning, differential
    diagnoses, first aid steps, and referral recommendation.

    The triage score is automatically adjusted upward if vital sign anomalies
    indicate a more urgent condition than the AI assessment.
    """
    # Step 1: Analyze vitals if provided
    vitals_analysis = None
    if request.vitals:
        vitals_analysis = analyze_vitals(
            request.vitals, request.patient.age
        )

    # Step 2: Run AI triage
    triage_result = run_triage(
        client=client,
        model=settings.LLM_MODEL,
        patient=request.patient,
        symptoms=request.symptoms_english,
        medical_entities=request.medical_entities,
        vitals_analysis=vitals_analysis,
    )

    # Step 3: Save to database
    session = create_triage_session(
        db=db,
        patient=request.patient,
        symptoms_english=request.symptoms_english,
        medical_entities=request.medical_entities,
        vitals=request.vitals,
        vitals_analysis=vitals_analysis,
        triage_result=triage_result,
    )

    return TriageResponse(
        session_id=session.id,
        triage=triage_result,
        vitals_analysis=(
            vitals_analysis.model_dump() if vitals_analysis else None
        ),
    )
