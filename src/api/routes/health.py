"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Status dict indicating API is running.
    """
    return {"status": "ok"}
