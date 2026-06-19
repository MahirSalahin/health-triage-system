"""Shared FastAPI dependencies for route handlers."""

from typing import Generator

from openai import OpenAI
from sqlmodel import Session

from app.core.ai_client import get_openai_client
from app.db.session import get_session


def get_db() -> Generator[Session, None, None]:
    """Yields a SQLModel database session."""
    yield from get_session()


def get_ai() -> OpenAI:
    """Returns the configured OpenAI client (Gemini-compat or real OpenAI)."""
    return get_openai_client()
