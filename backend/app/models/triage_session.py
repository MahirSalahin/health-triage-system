from datetime import datetime

from sqlmodel import SQLModel, Field


class TriageSession(SQLModel, table=True):
    """
    Stores all data collected during a single triage encounter.

    Patient demographics are embedded directly — no separate Patient table.
    Returning patients can be looked up by phone number, name, or date.
    """

    __tablename__ = "triage_session"

    id: int | None = Field(default=None, primary_key=True)

    # Patient demographics (embedded)
    patient_name: str = Field(max_length=255)
    patient_age: int = Field(ge=0, le=150)
    patient_sex: str = Field(max_length=10)  # "male" | "female" | "other"
    patient_phone: str | None = Field(
        default=None, max_length=20, index=True
    )

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
