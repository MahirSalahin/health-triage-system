"""Vitals analysis endpoints — Task 4."""

from fastapi import APIRouter

from app.schemas.vitals import VitalsInput, VitalsAnalysisResponse
from app.services.vitals_service import analyze_vitals

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.post("/analyze", response_model=VitalsAnalysisResponse)
def analyze_patient_vitals(
    vitals: VitalsInput,
    patient_age: int = 30,
):
    """
    Analyze patient vital signs and flag anomalies.

    Each vital is classified against clinical reference ranges as:
    NORMAL / MILD / MODERATE / SEVERE / CRITICAL.

    Pass `patient_age` to use pediatric ranges for children (age < 12).
    """
    return analyze_vitals(vitals, patient_age)
