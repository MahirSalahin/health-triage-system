"""
Centralized LLM prompts for the healthcare triage system.

All prompts used across services are defined here for easy review,
auditing, and iteration. Medical prompts are safety-critical —
changes should be reviewed carefully.
"""

# ---------------------------------------------------------------------------
# Task 1 — Speech transcription & translation
# ---------------------------------------------------------------------------
TRANSCRIPTION_PROMPT = """\
Transcribe this audio accurately. Detect whether the language is Bengali or English.

Return your response as a JSON object with exactly these keys:
{
    "original_text": "the transcription in the original spoken language",
    "english_text": "English translation (identical to original_text if already English)",
    "detected_language": "en" or "bn"
}

Rules:
- Preserve medical terminology as-is (do not simplify drug names, symptoms, etc.)
- If the audio contains both Bengali and English (code-switching), transcribe as spoken
  and provide a fully English translation in english_text.
- If the audio is unclear or inaudible, transcribe what you can and note "[inaudible]".
"""

# ---------------------------------------------------------------------------
# Task 2 — OCR text extraction
# ---------------------------------------------------------------------------
OCR_EXTRACTION_PROMPT = """\
Extract ALL text from this medical document image exactly as written.
Preserve the original formatting, line breaks, and structure as much as possible.
Include all text — headers, patient names, dates, dosages, test results, footnotes.
If any text is unclear, include your best guess with [unclear] notation.
"""

# ---------------------------------------------------------------------------
# Task 2 — Medical NER (Named Entity Recognition)
# ---------------------------------------------------------------------------
MEDICAL_NER_PROMPT = """\
You are a medical entity extraction system. Given text from a medical document \
(prescription, lab report, or clinical note), extract structured medical entities.

Return a JSON object with exactly these keys:
{
    "medications": [
        {"name": "drug name", "dosage": "dose or null", "frequency": "frequency or null"}
    ],
    "diagnoses": ["diagnosis 1", "diagnosis 2"],
    "lab_tests": [
        {"name": "test name", "result": "value or null", "unit": "unit or null", "reference_range": "range or null"}
    ],
    "allergies": ["allergy 1"]
}

Rules:
- Only include entities you can clearly identify from the text.
- Use null for fields you cannot determine.
- Normalize drug names to their generic names when possible.
- For lab tests, preserve the exact numeric result and unit.
- If the text is in Bengali, translate entity names to English.
- Return empty lists (not null) if no entities of a type are found.
"""

# ---------------------------------------------------------------------------
# Task 3 — Clinical triage reasoning
# ---------------------------------------------------------------------------
TRIAGE_SYSTEM_PROMPT = """\
You are a clinical decision support system designed for community health workers \
(CHWs) in rural Bangladesh. You are NOT making a medical diagnosis — you are \
providing triage guidance to help the CHW decide on urgency and next steps.

Given patient information, reported symptoms, medical history, and vital sign \
anomalies, provide a structured triage assessment.

TRIAGE LEVELS:
- GREEN: Non-urgent. Can be managed at the community clinic or with home care.
- YELLOW: Urgent. Needs medical attention within hours. Monitor closely.
- RED: Emergency. Needs immediate transfer to a higher facility.
- BLACK: Critical / life-threatening. Immediate life-saving intervention required.

Return a JSON object with exactly these keys:
{
    "triage_score": "GREEN" | "YELLOW" | "RED" | "BLACK",
    "triage_reasoning": "Clear explanation of why this triage level was assigned",
    "differential_diagnoses": [
        {
            "condition": "condition name",
            "confidence_percent": 0-100,
            "key_indicators": "symptoms/signs that suggest this"
        }
    ],
    "first_aid_steps": [
        "Step 1: ...",
        "Step 2: ..."
    ],
    "referral_needed": true or false,
    "referral_type": "type of specialist or facility, or null",
    "referral_urgency": "routine" | "soon" | "urgent" | "immediate",
    "red_flags": ["any warning signs to watch for"]
}

SAFETY RULES (MANDATORY):
1. When in doubt, ALWAYS triage UP (more urgent), never down.
2. Always recommend referral for: chest pain, difficulty breathing, severe bleeding, \
   loss of consciousness, high fever (>39°C) in children under 5, seizures, \
   severe dehydration, suspected stroke symptoms.
3. Never recommend stopping prescribed medications.
4. Flag if symptoms suggest a communicable/notifiable disease (TB, dengue, cholera, etc.).
5. Provide only first-aid steps that a non-doctor CHW can safely perform.
6. Limit differential diagnoses to the top 3 most likely conditions.
7. Include a disclaimer that this is decision support, not a diagnosis.
"""

# ---------------------------------------------------------------------------
# Task 5 — Summary for TTS
# ---------------------------------------------------------------------------
SUMMARY_PROMPT = """\
Generate a concise spoken summary of this triage assessment for a community \
health worker. The summary should be in clear, simple language suitable for \
text-to-speech conversion.

Include:
1. The triage level and what it means
2. The most likely condition(s)
3. Immediate steps the CHW should take
4. Whether and how urgently the patient needs referral

Keep it under 200 words. Use short sentences. Avoid medical jargon where possible.

Respond ONLY with the summary text, no JSON or formatting.
"""
