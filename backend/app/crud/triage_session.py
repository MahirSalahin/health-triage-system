"""CRUD operations for triage sessions."""

import json

from sqlmodel import Session, select

from app.models.triage_session import TriageSession
from app.schemas.patient import PatientInfo
from app.schemas.triage import TriageResult
from app.schemas.vitals import VitalsInput, VitalsAnalysisResponse
from app.schemas.document import MedicalEntities


def create_triage_session(
    db: Session,
    patient: PatientInfo,
    symptoms_original: str | None = None,
    symptoms_english: str | None = None,
    detected_language: str | None = None,
    extracted_text: str | None = None,
    medical_entities: MedicalEntities | None = None,
    vitals: VitalsInput | None = None,
    vitals_analysis: VitalsAnalysisResponse | None = None,
    triage_result: TriageResult | None = None,
) -> TriageSession:
    """Create and persist a new triage session."""
    session = TriageSession(
        patient_name=patient.name,
        patient_age=patient.age,
        patient_sex=patient.sex,
        patient_phone=patient.phone,
        symptoms_original=symptoms_original,
        symptoms_english=symptoms_english,
        detected_language=detected_language,
        extracted_text=extracted_text,
        medical_entities_json=(
            medical_entities.model_dump_json() if medical_entities else None
        ),
        vitals_json=vitals.model_dump_json() if vitals else None,
        vitals_anomalies_json=(
            vitals_analysis.model_dump_json() if vitals_analysis else None
        ),
        triage_result_json=(
            triage_result.model_dump_json() if triage_result else None
        ),
        triage_score=(
            triage_result.triage_score.value if triage_result else None
        ),
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_triage_session(db: Session, session_id: int) -> TriageSession | None:
    """Retrieve a triage session by ID."""
    return db.get(TriageSession, session_id)


def search_sessions_by_phone(
    db: Session, phone: str
) -> list[TriageSession]:
    """Find past triage sessions by patient phone number."""
    statement = (
        select(TriageSession)
        .where(TriageSession.patient_phone == phone)
        .order_by(TriageSession.created_at.desc())
    )
    return list(db.exec(statement).all())
