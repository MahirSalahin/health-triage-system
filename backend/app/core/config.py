from pydantic_settings import BaseSettings
from pydantic import BeforeValidator, PostgresDsn
from functools import lru_cache
from dotenv import load_dotenv
from typing import Any, Annotated

load_dotenv()


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    # App
    FRONTEND_URL: str = "http://localhost:8501"
    BACKEND_API_URL: str = "http://localhost:8000"
    BACKEND_CORS_ORIGINS: Annotated[
        list[str], BeforeValidator(parse_cors)
    ] = []

    # Database
    DATABASE_URL: PostgresDsn

    # AI — OpenAI SDK with Gemini compat
    GEMINI_API_KEY: str
    OPENAI_BASE_URL: str = (
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    LLM_MODEL: str = "gemini-3.5-flash"
    VISION_MODEL: str = "gemini-3.5-flash"

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
