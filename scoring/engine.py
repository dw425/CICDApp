"""Scoring Engine - Orchestrates all domain computations"""
import json
from pathlib import Path
from scoring.domains import golden_path, environment_promotion, pipeline_reliability
from scoring.domains import data_quality, security_governance, cost_efficiency

# Load weights
_weights_path = Path(__file__).parent.parent / "config" / "scoring_weights.json"
def load_weights():
    with open(_weights_path) as f:
        return json.load(f)["domains"]

DOMAIN_SCORERS = {
    "golden_path": golden_path,
    "environment_promotion": environment_promotion,
    "pipeline_reliability": pipeline_reliability,
    "data_quality": data_quality,
    "security_governance": security_governance,
    "cost_efficiency": cost_efficiency,
}

def compute_team_scores(team_data: dict) -> dict:
    """Compute all domain scores and composite for a team.

    Args:
        team_data: dict with keys matching data needed per domain:
            - deployment_events: DataFrame
            - pipeline_runs: DataFrame
            - table_constraints: DataFrame
            - dlt_expectations: DataFrame
            - cluster_policies: DataFrame
            - billing_usage: DataFrame

    Returns:
        dict with:
            - domain_scores: {domain: {raw_score, weighted_score, details}}
            - composite_score: float
            - maturity_tier: str
    """
    weights = load_weights()
    domain_scores = {}

    # Golden Path
    result = golden_path.compute_score(team_data.get("deployment_events"))
    domain_scores["golden_path"] = result

    # Environment Promotion
    result = environment_promotion.compute_score(
        team_data.get("pipeline_runs"),
        team_data.get("deployment_events")
    )
    domain_scores["environment_promotion"] = result

    # Pipeline Reliability
    result = pipeline_reliability.compute_score(team_data.get("pipeline_runs"))
    domain_scores["pipeline_reliability"] = result

    # Data Quality
    result = data_quality.compute_score(
        team_data.get("table_constraints"),
        team_data.get("dlt_expectations")
    )
    domain_scores["data_quality"] = result

    # Security & Governance
    result = security_governance.compute_score(team_data.get("cluster_policies"))
    domain_scores["security_governance"] = result

    # Cost Efficiency
    result = cost_efficiency.compute_score(team_data.get("billing_usage"))
    domain_scores["cost_efficiency"] = result

    # Compute composite: sum(raw_score * weight), redistribute NULL weights
    active_weight_sum = 0
    weighted_sum = 0

    for domain, score_data in domain_scores.items():
        raw = score_data.get("raw_score")
        weight = weights[domain]["weight"]
        if raw is not None:
            active_weight_sum += weight
            score_data["weight"] = weight
        else:
            score_data["weight"] = weight

    # Redistribute weights proportionally for non-null domains
    for domain, score_data in domain_scores.items():
        raw = score_data.get("raw_score")
        weight = weights[domain]["weight"]
        if raw is not None and active_weight_sum > 0:
            adjusted_weight = weight / active_weight_sum
            weighted_score = raw * adjusted_weight
            score_data["weighted_score"] = round(weighted_score, 2)
            weighted_sum += weighted_score
        else:
            score_data["weighted_score"] = 0

    composite_score = round(weighted_sum, 1)

    # Determine tier
    from ui.theme import get_tier
    maturity_tier = get_tier(composite_score)

    return {
        "domain_scores": domain_scores,
        "composite_score": composite_score,
        "maturity_tier": maturity_tier,
    }


def compute_all_teams(teams_data: dict) -> dict:
    """Compute scores for all teams.

    Args:
        teams_data: {team_id: team_data_dict}

    Returns:
        {team_id: scores_dict}
    """
    results = {}
    for team_id, data in teams_data.items():
        results[team_id] = compute_team_scores(data)
    return results
