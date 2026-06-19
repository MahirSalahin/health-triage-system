from datetime import datetime

from sqlmodel import SQLModel, Field


class TriageSession(SQLModel, table=True):
    """
    Stores all data collected during a single triage encounter.

    JSON fields store serialized Pydantic model data for flexibility —
    the structured schemas are defined in app/schemas/.
    """

    __tablename__ = "triage_session"

    id: int | None = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient.id")

    # Task 1 — Intake (voice/text)
    symptoms_original: str | None = Field(default=None)
    symptoms_english: str | None = Field(default=None)
    detected_language: str | None = Field(default=None, max_length=10)

    # Task 2 — Document scan (OCR + NER)
    extracted_text: str | None = Field(default=None)
    medical_entities_json: str | None = Field(default=None)

    # Task 4 — Vitals
    vitals_json: str | None = Field(default=None)
    vitals_anomalies_json: str | None = Field(default=None)

    # Task 3 — Triage result
    triage_result_json: str | None = Field(default=None)
    triage_score: str | None = Field(
        default=None, max_length=10
    )  # GREEN / YELLOW / RED / BLACK

    created_at: datetime = Field(default_factory=datetime.utcnow)
