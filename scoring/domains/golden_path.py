"""Golden Path Compliance Scoring (25%)
Measures the ratio of service-principal-driven (golden path) deployments
vs human-initiated deployments.
"""
import pandas as pd

def compute_score(deployment_events: pd.DataFrame) -> dict:
    """Compute golden path compliance score.

    Args:
        deployment_events: DataFrame with columns [is_golden_path, actor_type, status]

    Returns:
        dict with keys: raw_score, details
    """
    if deployment_events is None or deployment_events.empty:
        return {"raw_score": None, "details": {"total": 0, "golden": 0, "human": 0, "ratio": 0}}

    total = len(deployment_events)
    golden = deployment_events["is_golden_path"].sum() if "is_golden_path" in deployment_events.columns else 0
    human = total - golden
    ratio = golden / total if total > 0 else 0

    # Score: direct percentage (0-100)
    raw_score = round(ratio * 100, 1)

    return {
        "raw_score": raw_score,
        "details": {
            "total_deployments": int(total),
            "golden_path_count": int(golden),
            "human_count": int(human),
            "golden_path_ratio": round(ratio, 3),
        }
    }
