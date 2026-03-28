"""Assessment API endpoints — CRUD for maturity assessments."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class AssessmentCreate(BaseModel):
    org_id: str = Field(..., description="Organization identifier")
    assessor_name: str = Field(..., description="Name of the person running the assessment")
    team_id: Optional[str] = Field(None, description="Optional team scope")


class AssessmentResponse(BaseModel):
    assessment_id: str
    org_id: str
    status: str
    created_at: str
    dimensions_completed: int
    total_dimensions: int


class AnswerSubmit(BaseModel):
    dimension: str
    question_id: str
    answer: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None


@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
async def create_assessment(body: AssessmentCreate):
    """Create a new maturity assessment."""
    try:
        from data_layer.queries.compass import create_assessment as db_create
        assessment_id = db_create(body.org_id, body.assessor_name, body.team_id)
        return AssessmentResponse(
            assessment_id=assessment_id,
            org_id=body.org_id,
            status="in_progress",
            created_at=datetime.utcnow().isoformat(),
            dimensions_completed=0,
            total_dimensions=8,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str):
    """Retrieve assessment details and progress."""
    try:
        from data_layer.queries.compass import get_assessment as db_get
        result = db_get(assessment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments")
async def list_assessments(
    org_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List assessments with optional filters."""
    try:
        from data_layer.queries.compass import list_assessments as db_list
        return db_list(org_id=org_id, status=status, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assessments/{assessment_id}/answers")
async def submit_answer(assessment_id: str, body: AnswerSubmit):
    """Submit an answer for a specific question in an assessment."""
    try:
        from data_layer.queries.compass import save_answer as db_save
        db_save(assessment_id, body.dimension, body.question_id, body.answer, body.notes)
        return {"status": "saved", "assessment_id": assessment_id,
                "dimension": body.dimension, "question_id": body.question_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assessments/{assessment_id}/complete")
async def complete_assessment(assessment_id: str):
    """Mark an assessment as complete and trigger scoring."""
    try:
        from data_layer.queries.compass import complete_assessment as db_complete
        from scoring.engine import ScoringEngine
        result = db_complete(assessment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found")

        engine = ScoringEngine()
        scores = engine.compute_scores(result.get("responses", {}))
        return {"assessment_id": assessment_id, "status": "completed", "scores": scores}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
