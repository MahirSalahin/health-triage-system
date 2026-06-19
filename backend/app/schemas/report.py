from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Request to generate a PDF and/or audio report for a triage session."""

    session_id: int
    language: str = Field(
        default="en",
        pattern="^(en|bn)$",
        description="Language for TTS audio summary",
    )


class ReportResponse(BaseModel):
    """Response after report generation."""

    session_id: int
    pdf_url: str
    audio_url: str
