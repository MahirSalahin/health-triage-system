"""
Report generation service — Task 5 (PDF + summary).

Generates:
1. A spoken summary of the triage result via LLM
2. A professional PDF report using Jinja2 + WeasyPrint
"""

import json
import logging
import os

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from openai import OpenAI

from app.schemas.triage import TriageResult
from app.schemas.vitals import VitalsAnalysisResponse
from app.schemas.document import MedicalEntities
from app.utils.prompts import SUMMARY_PROMPT

logger = logging.getLogger(__name__)

# Resolve template directory relative to project root
_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "report_templates",
)


def generate_summary(
    client: OpenAI,
    model: str,
    triage_result: TriageResult,
    patient_name: str,
    patient_age: int,
) -> str:
    """
    Generate a concise spoken summary for TTS playback.

    Uses LLM to create a clear, simple-language summary suitable
    for text-to-speech conversion.
    """
    context = (
        f"Patient: {patient_name}, {patient_age} years old\n"
        f"Triage Score: {triage_result.triage_score.value}\n"
        f"Reasoning: {triage_result.triage_reasoning}\n"
    )

    if triage_result.differential_diagnoses:
        diagnoses_text = ", ".join(
            d.condition for d in triage_result.differential_diagnoses
        )
        context += f"Likely conditions: {diagnoses_text}\n"

    if triage_result.first_aid_steps:
        context += "First aid steps:\n"
        context += "\n".join(triage_result.first_aid_steps) + "\n"

    if triage_result.referral_needed:
        context += (
            f"Referral: {triage_result.referral_type} "
            f"(urgency: {triage_result.referral_urgency})\n"
        )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": context},
        ],
    )

    return response.choices[0].message.content or "Summary unavailable."


def generate_pdf_report(
    patient_name: str,
    patient_age: int,
    patient_sex: str,
    symptoms: str | None,
    triage_result: TriageResult,
    vitals_analysis: VitalsAnalysisResponse | None = None,
    medical_entities: MedicalEntities | None = None,
    created_at: str | None = None,
) -> bytes:
    """
    Generate a professional PDF report from triage session data.

    Uses a Jinja2 HTML template rendered to PDF via WeasyPrint.

    Returns:
        PDF bytes ready for download.
    """
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    template = env.get_template("patient_report.html")

    # Triage color mapping
    triage_colors = {
        "GREEN": "#22c55e",
        "YELLOW": "#eab308",
        "RED": "#ef4444",
        "BLACK": "#1f2937",
    }

    html_content = template.render(
        patient_name=patient_name,
        patient_age=patient_age,
        patient_sex=patient_sex,
        symptoms=symptoms or "Not recorded",
        triage_score=triage_result.triage_score.value,
        triage_color=triage_colors.get(
            triage_result.triage_score.value, "#6b7280"
        ),
        triage_reasoning=triage_result.triage_reasoning,
        diagnoses=triage_result.differential_diagnoses,
        first_aid_steps=triage_result.first_aid_steps,
        referral_needed=triage_result.referral_needed,
        referral_type=triage_result.referral_type,
        referral_urgency=triage_result.referral_urgency,
        red_flags=triage_result.red_flags,
        vitals_analysis=vitals_analysis,
        medical_entities=medical_entities,
        created_at=created_at or "N/A",
    )

    return HTML(string=html_content).write_pdf()
