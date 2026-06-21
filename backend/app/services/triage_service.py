"""
AI-powered clinical triage reasoning — Task 3.

Uses OpenAI SDK chat completions with JSON mode for structured triage output.
Combines patient symptoms, medical history, and vitals anomalies.
Works on both Gemini (via OpenAI-compat endpoint) and real OpenAI.
"""

import json
import logging

from openai import OpenAI

from app.schemas.triage import TriageResult, TriageLevel
from app.schemas.vitals import VitalsAnalysisResponse
from app.schemas.document import MedicalEntities
from app.schemas.patient import PatientInfo
from app.utils.prompts import TRIAGE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Maps vitals severity to minimum triage level
_VITALS_TRIAGE_FLOOR = {
    "CRITICAL": TriageLevel.RED,
    "SEVERE": TriageLevel.YELLOW,
    "MODERATE": TriageLevel.YELLOW,
}

# Triage level ordering for comparison
_TRIAGE_ORDER = {
    TriageLevel.GREEN: 0,
    TriageLevel.YELLOW: 1,
    TriageLevel.RED: 2,
    TriageLevel.BLACK: 3,
}


def _build_user_prompt(
    patient: PatientInfo,
    symptoms: str,
    medical_entities: MedicalEntities | None,
    vitals_analysis: VitalsAnalysisResponse | None,
) -> str:
    """Build the user message with all available clinical context."""
    parts = []

    # Patient demographics
    parts.append(
        f"PATIENT: {patient.name}, {patient.age} years old, {patient.sex}"
    )

    # Symptoms
    parts.append(f"\nREPORTED SYMPTOMS:\n{symptoms}")

    # Medical history from documents (if available)
    if medical_entities:
        history_parts = []
        if medical_entities.medications:
            meds = ", ".join(
                f"{m.name} ({m.dosage or 'unknown dose'})"
                for m in medical_entities.medications
            )
            history_parts.append(f"Current medications: {meds}")
        if medical_entities.diagnoses:
            history_parts.append(
                f"Known diagnoses: {', '.join(medical_entities.diagnoses)}"
            )
        if medical_entities.lab_tests:
            labs = ", ".join(
                f"{t.name}: {t.result or 'pending'} {t.unit or ''}"
                for t in medical_entities.lab_tests
            )
            history_parts.append(f"Lab results: {labs}")
        if medical_entities.allergies:
            history_parts.append(
                f"Allergies: {', '.join(medical_entities.allergies)}"
            )
        if history_parts:
            parts.append(
                "\nMEDICAL HISTORY (from documents):\n"
                + "\n".join(history_parts)
            )

    # Vitals anomalies (if available)
    if vitals_analysis and vitals_analysis.anomalies:
        anomaly_lines = [
            f"- {a.message}" for a in vitals_analysis.anomalies
        ]
        parts.append(
            f"\nVITAL SIGN ANOMALIES (overall: {vitals_analysis.overall_severity}):\n"
            + "\n".join(anomaly_lines)
        )
    elif vitals_analysis:
        parts.append("\nVITAL SIGNS: All within normal range.")

    return "\n".join(parts)


def _adjust_triage_for_vitals(
    result: TriageResult,
    vitals_analysis: VitalsAnalysisResponse | None,
) -> TriageResult:
    """
    Programmatically adjust triage score upward based on vital sign anomalies.

    Safety rule: vitals can only push triage UP (more urgent), never down.
    - Any CRITICAL vital → triage is at least RED
    - Any SEVERE vital → triage is at least YELLOW
    """
    if not vitals_analysis or not vitals_analysis.anomalies:
        return result

    floor = _VITALS_TRIAGE_FLOOR.get(vitals_analysis.overall_severity)
    if not floor:
        return result

    current_order = _TRIAGE_ORDER[result.triage_score]
    floor_order = _TRIAGE_ORDER[floor]

    if floor_order > current_order:
        logger.info(
            f"Adjusting triage from {result.triage_score} to {floor} "
            f"due to vitals severity: {vitals_analysis.overall_severity}"
        )
        result.triage_score = floor
        result.triage_reasoning += (
            f"\n\n[VITALS OVERRIDE] Triage elevated to {floor.value} "
            f"because vital signs show {vitals_analysis.overall_severity} "
            f"severity anomalies."
        )

    return result


def run_triage(
    client: OpenAI,
    model: str,
    patient: PatientInfo,
    symptoms: str,
    medical_entities: MedicalEntities | None = None,
    vitals_analysis: VitalsAnalysisResponse | None = None,
) -> TriageResult:
    """
    Run AI-powered clinical triage analysis.

    1. Sends patient data + symptoms + history + vitals to LLM
    2. Parses structured JSON triage result
    3. Programmatically adjusts score based on vitals anomalies

    Args:
        client: OpenAI client (Gemini-compat or real OpenAI).
        model: LLM model name.
        patient: Patient demographics.
        symptoms: English-language symptom description.
        medical_entities: Structured medical history from OCR (optional).
        vitals_analysis: Vitals anomaly analysis (optional).

    Returns:
        TriageResult with score, reasoning, diagnoses, first aid, referral.
    """
    user_prompt = _build_user_prompt(
        patient, symptoms, medical_entities, vitals_analysis
    )

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_json = response.choices[0].message.content or "{}"

    # Clean up common LLM JSON artifacts (markdown fences, trailing junk)
    cleaned = raw_json.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        
    # Extract the first complete JSON object using a brace-matching stack
    start_idx = cleaned.find("{")
    if start_idx != -1:
        stack = []
        for i in range(start_idx, len(cleaned)):
            if cleaned[i] == '{':
                stack.append('{')
            elif cleaned[i] == '}':
                if stack:
                    stack.pop()
                if not stack:
                    cleaned = cleaned[start_idx:i+1]
                    break

    try:
        parsed = json.loads(cleaned)
        result = TriageResult(**parsed)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse triage response: {e}. Raw: {raw_json}")
        # Fail safe: default to RED (err on the side of caution)
        result = TriageResult(
            triage_score=TriageLevel.RED,
            triage_reasoning="AI analysis failed to produce a valid result. "
            "Defaulting to RED (emergency) for safety. "
            "Please assess the patient manually.",
            referral_needed=True,
            referral_type="General physician",
            referral_urgency="urgent",
            red_flags=["AI triage failed — manual assessment required"],
        )

    # Safety adjustment: vitals can only push triage UP
    result = _adjust_triage_for_vitals(result, vitals_analysis)

    return result
