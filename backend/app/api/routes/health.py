"""Health check route — verifies the API is running."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "health-triage-api"}
