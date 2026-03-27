"""Pipeline Reliability Scoring (20%)
Composite: success_rate * 0.6 + mttr_score * 0.4
"""
import pandas as pd

def compute_score(pipeline_runs: pd.DataFrame) -> dict:
    """Compute pipeline reliability score.

    Args:
        pipeline_runs: DataFrame with columns [status, duration_seconds, run_date]
    """
    if pipeline_runs is None or pipeline_runs.empty:
        return {"raw_score": None, "details": {}}

    total = len(pipeline_runs)
    successes = len(pipeline_runs[pipeline_runs["status"] == "success"])
    failures = len(pipeline_runs[pipeline_runs["status"] == "failed"])

    # Success rate component (0-100)
    success_rate = (successes / total * 100) if total > 0 else 0

    # MTTR component: lower is better
    # Score based on average duration of failed runs (proxy for recovery time)
    failed_runs = pipeline_runs[pipeline_runs["status"] == "failed"]
    if not failed_runs.empty and "duration_seconds" in failed_runs.columns:
        avg_failure_duration = failed_runs["duration_seconds"].astype(float).mean()
        # Score: < 300s (5min) = 100, > 3600s (1hr) = 0, linear between
        mttr_score = max(0, min(100, 100 - (avg_failure_duration - 300) / (3600 - 300) * 100))
    else:
        mttr_score = 100  # No failures = perfect MTTR
        avg_failure_duration = 0

    # Composite: success_rate * 0.6 + mttr_score * 0.4
    raw_score = round(success_rate * 0.6 + mttr_score * 0.4, 1)

    return {
        "raw_score": raw_score,
        "details": {
            "total_runs": int(total),
            "successes": int(successes),
            "failures": int(failures),
            "success_rate": round(success_rate, 1),
            "mttr_score": round(mttr_score, 1),
            "avg_failure_duration_s": round(float(avg_failure_duration), 0) if not failed_runs.empty else 0,
        }
    }
