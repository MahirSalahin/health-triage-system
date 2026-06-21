import uuid
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.patient import PatientInfo
from app.schemas.vitals import VitalsInput
from app.schemas.document import MedicalEntities


class TriageLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    BLACK = "BLACK"


class Diagnosis(BaseModel):
    condition: str
    confidence_percent: int = Field(ge=0, le=100)
    key_indicators: str


class TriageResult(BaseModel):
    """Full AI triage analysis output."""

    triage_score: TriageLevel
    triage_reasoning: str
    differential_diagnoses: list[Diagnosis] = Field(default_factory=list)
    first_aid_steps: list[str] = Field(default_factory=list)
    referral_needed: bool
    referral_type: str | None = None
    referral_urgency: str | None = Field(
        default="routine",
        description="routine | soon | urgent | immediate",
    )
    red_flags: list[str] = Field(default_factory=list)


class TriageRequest(BaseModel):
    """Combined input for running triage analysis."""

    patient: PatientInfo
    symptoms_english: str
    medical_entities: MedicalEntities | None = None
    vitals: VitalsInput | None = None


class TriageResponse(BaseModel):
    """Response after running full triage."""

    session_id: uuid.UUID
    triage: TriageResult
    vitals_analysis: dict | None = None
