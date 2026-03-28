"""Scoring API endpoints — retrieve and compute maturity scores."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/scores/{assessment_id}")
async def get_scores(assessment_id: str):
    """Get computed scores for an assessment."""
    try:
        from data_layer.queries.compass import get_assessment_scores
        scores = get_assessment_scores(assessment_id)
        if not scores:
            raise HTTPException(status_code=404, detail="Scores not found")
        return scores
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores/team/{team_id}")
async def get_team_scores(team_id: str, limit: int = Query(10, ge=1, le=50)):
    """Get score history for a team."""
    try:
        from data_layer.queries.compass import get_team_score_history
        return get_team_score_history(team_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dora/{team_id}")
async def get_dora_metrics(team_id: str):
    """Get DORA metrics for a team."""
    try:
        from data_layer.queries.custom_tables import get_dora_metrics as db_dora
        result = db_dora(team_id)
        if not result:
            raise HTTPException(status_code=404, detail="No DORA data for team")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roi/calculate")
async def calculate_roi(params: dict):
    """Calculate ROI based on before/after scores and org context."""
    try:
        from analytics.roi_calculator import compute_roi
        before_scores = params.get("before_scores", {})
        after_scores = params.get("after_scores", {})
        org_context = params.get("org_context", {})
        result = compute_roi(before_scores, after_scores, org_context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
