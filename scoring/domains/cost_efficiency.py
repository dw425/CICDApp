"""Cost Efficiency Scoring (10%)
Ratio of jobs DBU to total DBU (higher jobs ratio = better).
"""
import pandas as pd

def compute_score(billing_usage: pd.DataFrame) -> dict:
    """Compute cost efficiency score.

    Args:
        billing_usage: DataFrame with columns [workload_type, dbu_consumed]
    """
    if billing_usage is None or billing_usage.empty:
        return {"raw_score": None, "details": {}}

    # Sum DBU by workload type
    if "workload_type" not in billing_usage.columns or "dbu_consumed" not in billing_usage.columns:
        return {"raw_score": None, "details": {}}

    usage_by_type = billing_usage.groupby("workload_type")["dbu_consumed"].sum()
    total_dbu = usage_by_type.sum()

    jobs_dbu = usage_by_type.get("JOBS", 0) + usage_by_type.get("DLT", 0)
    interactive_dbu = usage_by_type.get("INTERACTIVE", 0)
    sql_dbu = usage_by_type.get("SQL", 0)

    # Jobs ratio: higher is better (automated > interactive)
    jobs_ratio = jobs_dbu / total_dbu if total_dbu > 0 else 0
    raw_score = round(jobs_ratio * 100, 1)

    return {
        "raw_score": raw_score,
        "details": {
            "total_dbu": round(float(total_dbu), 1),
            "jobs_dbu": round(float(jobs_dbu), 1),
            "interactive_dbu": round(float(interactive_dbu), 1),
            "sql_dbu": round(float(sql_dbu), 1),
            "jobs_ratio": round(jobs_ratio, 3),
        }
    }
