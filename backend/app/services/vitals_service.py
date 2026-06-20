"""
Vital sign anomaly detection using clinical reference ranges.

No AI/API dependency — uses well-established medical thresholds.
Differentiates between adult and pediatric ranges.
"""

from app.schemas.vitals import VitalsInput, VitalAnomaly, VitalsAnalysisResponse


# Severity ordering for comparison
SEVERITY_ORDER = {
    "NORMAL": 0,
    "MILD": 1,
    "MODERATE": 2,
    "SEVERE": 3,
    "CRITICAL": 4,
}

# ---------------------------------------------------------------------------
# Adult reference ranges (age >= 12)
# Each vital has a list of (low, high, severity) ranges checked in order.
# The FIRST matching range wins, so order matters (most specific first).
# ---------------------------------------------------------------------------
ADULT_RANGES: dict[str, dict] = {
    "systolic_bp": {
        "unit": "mmHg",
        "ranges": [
            (90, 120, "NORMAL"),
            # High
            (120, 140, "MILD"),
            (140, 160, "MODERATE"),
            (160, 180, "SEVERE"),
            (180, 300, "CRITICAL"),
            # Low
            (70, 90, "MILD"),
            (50, 70, "SEVERE"),
            (0, 50, "CRITICAL"),
        ],
    },
    "diastolic_bp": {
        "unit": "mmHg",
        "ranges": [
            (60, 80, "NORMAL"),
            # High
            (80, 90, "MILD"),
            (90, 100, "MODERATE"),
            (100, 110, "SEVERE"),
            (110, 200, "CRITICAL"),
            # Low
            (40, 60, "MILD"),
            (0, 40, "SEVERE"),
        ],
    },
    "heart_rate": {
        "unit": "bpm",
        "ranges": [
            (60, 100, "NORMAL"),
            # High
            (100, 110, "MILD"),
            (110, 130, "MODERATE"),
            (130, 150, "SEVERE"),
            (150, 300, "CRITICAL"),
            # Low
            (50, 60, "MILD"),
            (40, 50, "MODERATE"),
            (30, 40, "SEVERE"),
            (0, 30, "CRITICAL"),
        ],
    },
    "temperature_c": {
        "unit": "°C",
        "ranges": [
            (36.1, 37.2, "NORMAL"),
            # High (fever)
            (37.2, 38.0, "MILD"),
            (38.0, 39.0, "MODERATE"),
            (39.0, 40.0, "SEVERE"),
            (40.0, 45.0, "CRITICAL"),
            # Low (hypothermia)
            (35.5, 36.1, "MILD"),
            (35.0, 35.5, "MODERATE"),
            (34.0, 35.0, "SEVERE"),
            (25.0, 34.0, "CRITICAL"),
        ],
    },
    "spo2": {
        "unit": "%",
        "ranges": [
            (95, 100, "NORMAL"),
            (92, 95, "MILD"),
            (88, 92, "MODERATE"),
            (85, 88, "SEVERE"),
            (0, 85, "CRITICAL"),
        ],
    },
    "blood_glucose_mgdl": {
        "unit": "mg/dL",
        "ranges": [
            (70, 140, "NORMAL"),
            # High
            (140, 180, "MILD"),
            (180, 250, "MODERATE"),
            (250, 400, "SEVERE"),
            (400, 800, "CRITICAL"),
            # Low (hypoglycemia)
            (54, 70, "MILD"),
            (40, 54, "SEVERE"),
            (0, 40, "CRITICAL"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Pediatric reference ranges (age < 12)
# Children have significantly different normal ranges.
# ---------------------------------------------------------------------------
PEDIATRIC_RANGES: dict[str, dict] = {
    "systolic_bp": {
        "unit": "mmHg",
        "ranges": [
            (80, 110, "NORMAL"),
            (110, 130, "MILD"),
            (130, 150, "MODERATE"),
            (150, 300, "SEVERE"),
            (60, 80, "MILD"),
            (0, 60, "CRITICAL"),
        ],
    },
    "diastolic_bp": {
        "unit": "mmHg",
        "ranges": [
            (50, 70, "NORMAL"),
            (70, 90, "MILD"),
            (90, 110, "MODERATE"),
            (110, 200, "SEVERE"),
            (30, 50, "MILD"),
            (0, 30, "CRITICAL"),
        ],
    },
    "heart_rate": {
        "unit": "bpm",
        "ranges": [
            (70, 120, "NORMAL"),  # Wide normal range for children
            (120, 140, "MILD"),
            (140, 170, "MODERATE"),
            (170, 200, "SEVERE"),
            (200, 300, "CRITICAL"),
            (60, 70, "MILD"),
            (40, 60, "MODERATE"),
            (0, 40, "CRITICAL"),
        ],
    },
    "temperature_c": {
        "unit": "°C",
        "ranges": [
            (36.5, 37.5, "NORMAL"),
            (37.5, 38.0, "MILD"),
            (38.0, 39.0, "MODERATE"),
            # High fever in children is more dangerous
            (39.0, 40.0, "SEVERE"),
            (40.0, 45.0, "CRITICAL"),
            (35.5, 36.5, "MILD"),
            (35.0, 35.5, "MODERATE"),
            (25.0, 35.0, "CRITICAL"),
        ],
    },
    "spo2": {
        "unit": "%",
        "ranges": [
            (95, 100, "NORMAL"),
            (92, 95, "MILD"),
            (88, 92, "MODERATE"),
            (85, 88, "SEVERE"),
            (0, 85, "CRITICAL"),
        ],
    },
    "blood_glucose_mgdl": {
        "unit": "mg/dL",
        "ranges": [
            (70, 140, "NORMAL"),
            (140, 200, "MILD"),
            (200, 300, "MODERATE"),
            (300, 800, "SEVERE"),
            (50, 70, "MILD"),
            (40, 50, "SEVERE"),
            (0, 40, "CRITICAL"),
        ],
    },
}

# Human-readable labels for vital names
VITAL_LABELS = {
    "systolic_bp": "Systolic Blood Pressure",
    "diastolic_bp": "Diastolic Blood Pressure",
    "heart_rate": "Heart Rate",
    "temperature_c": "Body Temperature",
    "spo2": "Oxygen Saturation (SpO2)",
    "blood_glucose_mgdl": "Blood Glucose",
}


def _classify_vital(
    name: str, value: float, ranges: dict[str, dict]
) -> tuple[str, str, str]:
    """
    Classify a single vital sign reading against reference ranges.

    Returns: (severity, unit, message)
    """
    vital_config = ranges.get(name)
    if not vital_config:
        return "NORMAL", "", f"Unknown vital: {name}"

    unit = vital_config["unit"]
    label = VITAL_LABELS.get(name, name)

    for low, high, severity in vital_config["ranges"]:
        if low <= value <= high:
            if severity == "NORMAL":
                return "NORMAL", unit, f"{label} is normal ({value} {unit})"

            # Determine if it's high or low relative to normal
            normal_range = vital_config["ranges"][0]  # First entry is NORMAL
            normal_mid = (normal_range[0] + normal_range[1]) / 2
            direction = "high" if value > normal_mid else "low"

            return (
                severity,
                unit,
                f"{label} is {severity.lower()} — "
                f"{value} {unit} ({direction})",
            )

    # Value didn't match any range — treat as critical
    return (
        "CRITICAL",
        vital_config["unit"],
        f"{label} is out of all expected ranges — {value} {unit}",
    )


def analyze_vitals(vitals: VitalsInput, patient_age: int) -> VitalsAnalysisResponse:
    """
    Analyze all provided vitals and return anomalies.

    Args:
        vitals: Patient vital sign readings (None fields are skipped).
        patient_age: Used to select adult vs pediatric reference ranges.

    Returns:
        VitalsAnalysisResponse with list of anomalies and overall severity.
    """
    ranges = PEDIATRIC_RANGES if patient_age < 12 else ADULT_RANGES
    anomalies: list[VitalAnomaly] = []

    # Iterate over all provided (non-None) vitals
    vitals_dict = vitals.model_dump(exclude_none=True)

    for vital_name, value in vitals_dict.items():
        severity, unit, message = _classify_vital(vital_name, value, ranges)

        if severity != "NORMAL":
            anomalies.append(
                VitalAnomaly(
                    vital_name=vital_name,
                    value=value,
                    unit=unit,
                    severity=severity,
                    message=message,
                )
            )

    # Overall severity = worst individual severity
    if anomalies:
        overall = max(
            anomalies, key=lambda a: SEVERITY_ORDER.get(a.severity, 0)
        ).severity
    else:
        overall = "NORMAL"

    return VitalsAnalysisResponse(
        anomalies=anomalies,
        overall_severity=overall,
    )
