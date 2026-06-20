import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.vitals import router as vitals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown: nothing to clean up for now


app = FastAPI(
    title="Rural Healthcare Triage API",
    description="AI-powered triage and decision support for community health workers.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Routes ---
app.include_router(health_router, prefix="/api")
app.include_router(vitals_router, prefix="/api")

# Feature routes will be added here as they're built:
# app.include_router(intake_router, prefix="/api")
# app.include_router(documents_router, prefix="/api")
# app.include_router(triage_router, prefix="/api")
# app.include_router(reports_router, prefix="/api")

