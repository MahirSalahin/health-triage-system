from pydantic import BaseModel, Field


class Medication(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None


class LabTest(BaseModel):
    name: str
    result: str | None = None
    unit: str | None = None
    reference_range: str | None = None


class MedicalEntities(BaseModel):
    """Structured medical entities extracted via NER from OCR text."""

    medications: list[Medication] = Field(default_factory=list)
    diagnoses: list[str] = Field(default_factory=list)
    lab_tests: list[LabTest] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class DocumentScanResponse(BaseModel):
    """Response after scanning a medical document."""

    raw_text: str = Field(description="Raw OCR-extracted text")
    entities: MedicalEntities
