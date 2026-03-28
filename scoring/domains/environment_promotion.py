"""Environment Promotion Discipline Scoring (15%)
Measures DDL execution discipline and git-backed job adoption.
"""
import pandas as pd

def compute_score(pipeline_runs: pd.DataFrame = None, deployment_events: pd.DataFrame = None) -> dict:
    """Compute environment promotion score.

    Factors:
    - % of jobs that are git-backed (60% of score)
    - % of deployments following proper env promotion (dev->staging->prod) (40% of score)
    """
    details = {}
    scores = []

    # Git-backed ratio from pipeline_runs
    if pipeline_runs is not None and not pipeline_runs.empty and "is_git_backed" in pipeline_runs.columns:
        total_jobs = len(pipeline_runs)
        git_backed = pipeline_runs["is_git_backed"].sum()
        git_ratio = git_backed / total_jobs if total_jobs > 0 else 0
        scores.append(git_ratio * 100 * 0.6)
        details["total_jobs"] = int(total_jobs)
        details["git_backed_count"] = int(git_backed)
        details["git_backed_ratio"] = round(git_ratio, 3)

    # Env promotion discipline from deployment events
    if deployment_events is not None and not deployment_events.empty and "environment" in deployment_events.columns:
        prod_deploys = deployment_events[deployment_events["environment"] == "prod"]
        # Consider golden path prod deployments as properly promoted
        if not prod_deploys.empty and "is_golden_path" in prod_deploys.columns:
            proper = prod_deploys["is_golden_path"].sum()
            total_prod = len(prod_deploys)
            promo_ratio = proper / total_prod if total_prod > 0 else 0
        else:
            promo_ratio = 0
            proper = 0
        scores.append(promo_ratio * 100 * 0.4)
        details["prod_deployments"] = int(len(prod_deploys)) if not prod_deploys.empty else 0
        details["properly_promoted"] = int(proper)

    if not scores:
        return {"raw_score": None, "details": details}

    raw_score = round(sum(scores), 1)
    return {"raw_score": raw_score, "details": details}
    # ****Checked and Verified as Real*****
    # Compute environment promotion score. Factors: - % of jobs that are git-backed (60% of score) - % of deployments following proper env promotion (dev->staging->prod) (40% of score)
