from pydantic import BaseModel, Field


class VitalsInput(BaseModel):
    """Patient vital signs entered by the CHW."""

    systolic_bp: float | None = Field(
        default=None, ge=0, le=300, description="Systolic blood pressure (mmHg)"
    )
    diastolic_bp: float | None = Field(
        default=None, ge=0, le=200, description="Diastolic blood pressure (mmHg)"
    )
    heart_rate: float | None = Field(
        default=None, ge=0, le=300, description="Heart rate (bpm)"
    )
    temperature_c: float | None = Field(
        default=None, ge=25, le=45, description="Body temperature (°C)"
    )
    spo2: float | None = Field(
        default=None, ge=0, le=100, description="Oxygen saturation (%)"
    )
    blood_glucose_mgdl: float | None = Field(
        default=None, ge=0, le=800, description="Blood glucose (mg/dL)"
    )


class VitalAnomaly(BaseModel):
    """A single vital sign anomaly detected."""

    vital_name: str
    value: float
    unit: str
    severity: str = Field(
        description="NORMAL | MILD | MODERATE | SEVERE | CRITICAL"
    )
    message: str = Field(description="Human-readable explanation")


class VitalsAnalysisResponse(BaseModel):
    """Response after analyzing patient vitals."""

    anomalies: list[VitalAnomaly] = Field(default_factory=list)
    overall_severity: str = Field(
        default="NORMAL",
        description="Worst severity across all vitals",
    )
