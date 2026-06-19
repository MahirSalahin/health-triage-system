from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    """Request body for creating a new patient."""

    name: str = Field(..., max_length=255, examples=["রহিম উদ্দিন"])
    age: int = Field(..., ge=0, le=150, examples=[45])
    sex: str = Field(..., pattern="^(male|female|other)$", examples=["male"])


class PatientRead(BaseModel):
    """Response body for a patient record."""

    id: int
    name: str
    age: int
    sex: str
