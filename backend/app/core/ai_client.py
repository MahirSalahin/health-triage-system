from openai import OpenAI

from app.core.config import settings


def get_openai_client() -> OpenAI:
    """
    Returns an OpenAI client pointed at Gemini's OpenAI-compatible endpoint.

    Migration to OpenAI:
        - Remove `base_url`
        - Change `api_key` to your OpenAI key
        - Update model names in config (e.g. "gpt-4o")
    """
    return OpenAI(
        api_key=settings.GEMINI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
