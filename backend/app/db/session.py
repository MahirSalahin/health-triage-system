from sqlmodel import create_engine, Session

from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL), echo=False)


def get_session():
    """FastAPI dependency that yields a SQLModel session."""
    with Session(engine) as session:
        yield session
