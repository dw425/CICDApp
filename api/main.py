"""FastAPI application — REST API for CI/CD Maturity Intelligence.

Provides programmatic access to assessments, scores, DORA metrics,
golden path data, and ROI calculations.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.assessments import router as assessments_router
from api.routes.scores import router as scores_router
from api.routes.golden_path import router as golden_path_router
from api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    yield


app = FastAPI(
    title="CI/CD Maturity Intelligence API",
    version="3.0.0",
    description="REST API for pipeline maturity assessments, scoring, and analytics.",
    lifespan=lifespan,
)

# CORS
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:8050,http://localhost:8070").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, tags=["health"])
app.include_router(assessments_router, prefix="/api/v1", tags=["assessments"])
app.include_router(scores_router, prefix="/api/v1", tags=["scores"])
app.include_router(golden_path_router, prefix="/api/v1", tags=["golden-path"])
