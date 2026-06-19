from pydantic import BaseModel, Field


class TextIntakeRequest(BaseModel):
    """Request body for text-based symptom intake."""

    text: str = Field(
        ...,
        min_length=1,
        examples=["আমার মাথা ব্যথা এবং জ্বর আছে"],
    )
    language: str = Field(
        default="auto",
        pattern="^(auto|en|bn)$",
        description="Source language: 'auto' for detection, 'en', or 'bn'.",
    )


class IntakeResponse(BaseModel):
    """Response after voice or text intake processing."""

    original_text: str
    english_text: str
    detected_language: str = Field(
        description="ISO 639-1 code: 'en' or 'bn'"
    )
