"""Golden Path API endpoints — deployment classification and adoption metrics."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/golden-path/adoption")
async def get_adoption_metrics(team_id: Optional[str] = Query(None)):
    """Get golden path adoption metrics, optionally filtered by team."""
    try:
        from ingestion.golden_path_classifier import GoldenPathClassifier
        from data_layer.queries.custom_tables import get_deployment_events, get_teams

        events_df = get_deployment_events()
        if events_df.empty:
            return {"total_deployments": 0, "adoption_pct": 0,
                    "standard_count": 0, "non_standard_count": 0}

        teams_df = get_teams()
        team_lookup = dict(zip(teams_df["team_id"], teams_df["team_name"])) if not teams_df.empty else {}

        classifier = GoldenPathClassifier(team_registry={tid: [] for tid in team_lookup})
        events = events_df.to_dict("records")
        classified = classifier.classify_batch(events)
        metrics = classifier.compute_adoption_metrics(classified)

        if team_id:
            team_data = metrics.get("by_team", {}).get(team_id)
            if not team_data:
                raise HTTPException(status_code=404, detail=f"No data for team {team_id}")
            return {"team_id": team_id, **team_data}

        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/golden-path/classify")
async def classify_deployment(event: dict):
    """Classify a single deployment event as standard/non-standard."""
    try:
        from ingestion.golden_path_classifier import GoldenPathClassifier
        classifier = GoldenPathClassifier()
        result = classifier.classify(event)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/golden-path/violations")
async def get_violations(limit: int = Query(20, ge=1, le=100)):
    """Get recent non-standard deployments."""
    try:
        from ingestion.golden_path_classifier import GoldenPathClassifier
        from data_layer.queries.custom_tables import get_deployment_events

        events_df = get_deployment_events()
        if events_df.empty:
            return []

        classifier = GoldenPathClassifier()
        classified = classifier.classify_batch(events_df.to_dict("records"))
        violations = [e for e in classified if e["classification"] == "non_standard"]
        return violations[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
