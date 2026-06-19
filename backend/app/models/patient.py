from datetime import datetime

from sqlmodel import SQLModel, Field


class Patient(SQLModel, table=True):
    """Patient demographic information."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    age: int = Field(ge=0, le=150)
    sex: str = Field(max_length=10)  # "male" | "female" | "other"
    created_at: datetime = Field(default_factory=datetime.utcnow)
