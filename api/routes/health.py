"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check including database and connector status."""
    db_ok = False
    try:
        from data_layer.db import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "components": {
            "database": "ok" if db_ok else "unavailable",
            "dash_app": "ok",
        },
    }
