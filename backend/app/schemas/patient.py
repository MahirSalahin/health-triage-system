from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    """Patient demographics — embedded in triage requests, not a separate entity."""

    name: str = Field(..., max_length=255, examples=["রহিম উদ্দিন"])
    age: int = Field(..., ge=0, le=150, examples=[45])
    sex: str = Field(..., pattern="^(male|female|other)$", examples=["male"])
    phone: str | None = Field(
        default=None,
        max_length=20,
        examples=["01712345678"],
        description="Optional phone number for returning-patient lookup",
    )
