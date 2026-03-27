"""
Scoring Engine for Pipeline Compass.

Two-layer scoring:
  Layer 1: Raw 0-100 score per dimension (internal precision)
  Layer 2: L1-L5 maturity tier mapping (external communication)

Score aggregation uses weighted geometric mean to prevent
high scores in one dimension from masking critical gaps.
"""

import math
from typing import Optional

from compass.question_bank.loader import (
    load_all_dimensions,
    get_question,
    get_questions_for_dimension,
    get_core_dimensions,
    get_databricks_dimensions,
)


# ── Tier Mapping ──

TIER_MAP = [
    (0, 20, 1, "Initial"),
    (21, 40, 2, "Managed"),
    (41, 60, 3, "Defined"),
    (61, 80, 4, "Optimized"),
    (81, 100, 5, "Elite"),
]

TIER_COLORS = {
    1: "#EF4444",   # Red
    2: "#F97316",   # Orange
    3: "#EAB308",   # Yellow
    4: "#22C55E",   # Green
    5: "#3B82F6",   # Blue
}

TIER_LABELS = {1: "Initial", 2: "Managed", 3: "Defined", 4: "Optimized", 5: "Elite"}


# ── Weight Profiles ──

WEIGHT_PROFILES = {
    "balanced": {
        "build_integration": 0.12,
        "testing_quality": 0.14,
        "deployment_release": 0.14,
        "security_compliance": 0.12,
        "observability": 0.10,
        "iac_configuration": 0.10,
        "artifact_management": 0.08,
        "developer_experience": 0.10,
        "pipeline_governance": 0.10,
    },
    "data_engineering": {
        "build_integration": 0.10,
        "testing_quality": 0.20,
        "deployment_release": 0.15,
        "security_compliance": 0.08,
        "observability": 0.10,
        "iac_configuration": 0.08,
        "artifact_management": 0.05,
        "developer_experience": 0.12,
        "pipeline_governance": 0.12,
    },
    "financial_services": {
        "build_integration": 0.10,
        "testing_quality": 0.15,
        "deployment_release": 0.10,
        "security_compliance": 0.20,
        "observability": 0.12,
        "iac_configuration": 0.08,
        "artifact_management": 0.10,
        "developer_experience": 0.05,
        "pipeline_governance": 0.10,
    },
    "startup": {
        "build_integration": 0.15,
        "testing_quality": 0.12,
        "deployment_release": 0.20,
        "security_compliance": 0.05,
        "observability": 0.10,
        "iac_configuration": 0.12,
        "artifact_management": 0.06,
        "developer_experience": 0.15,
        "pipeline_governance": 0.05,
    },
    "federal_government": {
        "build_integration": 0.10,
        "testing_quality": 0.12,
        "deployment_release": 0.10,
        "security_compliance": 0.20,
        "observability": 0.08,
        "iac_configuration": 0.10,
        "artifact_management": 0.10,
        "developer_experience": 0.08,
        "pipeline_governance": 0.12,
    },
}

WEIGHT_PROFILE_LABELS = {
    "balanced": "Balanced (Default)",
    "data_engineering": "Data Engineering Focus",
    "financial_services": "Financial Services / Regulated",
    "startup": "Startup / Fast-Shipping",
    "federal_government": "Federal Government / IL4+",
}


def score_to_tier(score: float) -> tuple:
    """Map a 0-100 score to an (level, label) tuple."""
    for low, high, level, label in TIER_MAP:
        if low <= score <= high:
            return level, label
    return 5, "Elite"


def tier_color(level: int) -> str:
    """Get the color for a maturity level."""
    return TIER_COLORS.get(level, "#888888")


def compute_question_score(question: dict, response_value: dict) -> float:
    """
    Map a single question response to a 0-100 score.

    Args:
        question: The question definition from the YAML bank.
        response_value: The response dict, e.g. {"value": 3} or {"values": ["a","b"]}.

    Returns:
        Score between 0 and 100.
    """
    qtype = question.get("type", "likert")

    if qtype == "freeform":
        return 0.0

    if qtype in ("likert", "single_select"):
        options = question.get("options", [])
        if not options:
            return 0.0
        values = [o["value"] for o in options]
        min_val = min(values)
        max_val = max(values)
        val = response_value.get("value", min_val)
        if max_val == min_val:
            return 100.0 if val >= max_val else 0.0
        return round(((val - min_val) / (max_val - min_val)) * 100, 2)

    if qtype == "binary":
        val = response_value.get("value", False)
        return 100.0 if val else 0.0

    if qtype == "multi_select":
        selected = response_value.get("values", [])
        # Filter out "none" from selected
        selected = [s for s in selected if s != "none"]
        scoring = question.get("scoring", {})
        per_sel = scoring.get("per_selection")
        if per_sel:
            return min(len(selected) * per_sel, 100)
        total_options = len([o for o in question.get("options", []) if o.get("value") != "none"])
        if total_options == 0:
            return 0.0
        return round((len(selected) / total_options) * 100, 2)

    return 0.0


def score_dimension(
    dimension_id: str,
    responses: dict,
    sub_dimension: Optional[str] = None,
) -> dict:
    """
    Score a single dimension from its question responses.

    Args:
        dimension_id: The dimension key (e.g. "build_integration" or "databricks.dabs_maturity").
        responses: Dict of {question_id: {response_type, response_value, ...}}.
        sub_dimension: Optional sub-dimension for Databricks.

    Returns:
        Dict with: raw_score, level, label, color, question_count, answered_count,
        question_scores (per-question breakdown).
    """
    load_all_dimensions()
    questions = get_questions_for_dimension(dimension_id)

    if not questions:
        return {
            "raw_score": 0,
            "level": 1,
            "label": "Initial",
            "color": TIER_COLORS[1],
            "question_count": 0,
            "answered_count": 0,
            "question_scores": [],
        }

    total_weight = 0
    weighted_sum = 0
    answered = 0
    question_scores = []

    for q in questions:
        qid = q["id"]
        weight = q.get("weight", 1)

        if qid in responses:
            resp = responses[qid]
            resp_val = resp.get("response_value", resp)
            if isinstance(resp_val, (int, float)):
                resp_val = {"value": resp_val}

            score = compute_question_score(q, resp_val)
            weighted_sum += score * weight
            total_weight += weight
            answered += 1

            question_scores.append({
                "question_id": qid,
                "text": q.get("text", ""),
                "weight": weight,
                "response_value": resp_val,
                "score": score,
            })
        else:
            question_scores.append({
                "question_id": qid,
                "text": q.get("text", ""),
                "weight": weight,
                "response_value": None,
                "score": None,
            })

    raw_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0
    level, label = score_to_tier(raw_score)

    return {
        "raw_score": raw_score,
        "level": level,
        "label": label,
        "color": TIER_COLORS[level],
        "question_count": len(questions),
        "answered_count": answered,
        "question_scores": question_scores,
    }


def score_all_dimensions(
    responses: dict,
    uses_databricks: bool = False,
) -> dict:
    """
    Score all dimensions from assessment responses.

    Args:
        responses: Dict of {question_id: response_dict}.
        uses_databricks: Whether to include Databricks sub-dimensions.

    Returns:
        Dict keyed by dimension_id with score dicts.
    """
    load_all_dimensions()
    results = {}

    # Core dimensions
    for dim in get_core_dimensions():
        dim_id = dim["dimension"]
        results[dim_id] = score_dimension(dim_id, responses)
        results[dim_id]["display_name"] = dim["display_name"]
        results[dim_id]["icon"] = dim.get("icon", "circle")

    # Databricks sub-dimensions
    if uses_databricks:
        for dim in get_databricks_dimensions():
            sub = dim.get("sub_dimension", "")
            key = f"databricks.{sub}"
            results[key] = score_dimension(key, responses, sub_dimension=sub)
            results[key]["display_name"] = dim["display_name"]
            results[key]["icon"] = dim.get("icon", "database")
            results[key]["is_databricks"] = True

    return results


def compute_composite_score(
    dimension_scores: dict,
    profile: str = "balanced",
    custom_weights: Optional[dict] = None,
) -> dict:
    """
    Compute overall composite score using weighted geometric mean.

    Geometric mean prevents a high score in one dimension from
    compensating for a critical gap in another.

    Args:
        dimension_scores: Dict of {dim_id: {"raw_score": float, ...}}.
        profile: Weight profile name.
        custom_weights: Override weight dict.

    Returns:
        Dict with: overall_score, overall_level, overall_label, overall_color,
        dimension_breakdown.
    """
    weights = custom_weights or WEIGHT_PROFILES.get(profile, WEIGHT_PROFILES["balanced"])

    log_sum = 0.0
    weight_sum = 0.0
    dimension_breakdown = {}

    for dim_id, score_data in dimension_scores.items():
        # Skip Databricks sub-dimensions in composite (they enrich but don't drive top-level)
        if "." in dim_id:
            continue

        raw = score_data.get("raw_score", 0) if isinstance(score_data, dict) else score_data
        w = weights.get(dim_id, 0)

        if w > 0 and raw >= 0:
            log_sum += w * math.log(raw + 1)
            weight_sum += w

        level, label = score_to_tier(raw)
        dimension_breakdown[dim_id] = {
            "score": raw,
            "level": level,
            "label": label,
            "color": TIER_COLORS[level],
            "weight": w,
            "display_name": score_data.get("display_name", dim_id) if isinstance(score_data, dict) else dim_id,
        }

    composite = math.exp(log_sum / weight_sum) - 1 if weight_sum > 0 else 0
    composite = round(min(max(composite, 0), 100), 2)
    overall_level, overall_label = score_to_tier(composite)

    return {
        "overall_score": composite,
        "overall_level": overall_level,
        "overall_label": overall_label,
        "overall_color": TIER_COLORS[overall_level],
        "weight_profile": profile,
        "dimension_breakdown": dimension_breakdown,
    }


def collect_indicators(responses: dict) -> set:
    """
    Collect all indicator strings from assessment responses.

    Used by the anti-pattern engine.
    """
    load_all_dimensions()
    indicators = set()

    for qid, resp in responses.items():
        q = get_question(qid)
        if not q:
            continue

        resp_val = resp.get("response_value", resp)
        qtype = q.get("type", "likert")

        if qtype in ("likert", "single_select"):
            val = resp_val.get("value") if isinstance(resp_val, dict) else resp_val
            for opt in q.get("options", []):
                if opt["value"] == val:
                    indicators.update(opt.get("indicators", []))
                    break

        elif qtype == "binary":
            val = resp_val.get("value", False) if isinstance(resp_val, dict) else resp_val
            for opt in q.get("options", []):
                if opt["value"] == val:
                    indicators.update(opt.get("indicators", []))
                    break

        elif qtype == "multi_select":
            selected = resp_val.get("values", []) if isinstance(resp_val, dict) else []
            for opt in q.get("options", []):
                if opt["value"] in selected:
                    indicators.update(opt.get("indicators", []))

    return indicators


def full_score_assessment(
    responses: dict,
    weight_profile: str = "balanced",
    uses_databricks: bool = False,
) -> dict:
    """
    Run the complete scoring pipeline for an assessment.

    Returns:
        Dict with: dimension_scores, composite, indicators.
    """
    dim_scores = score_all_dimensions(responses, uses_databricks)
    composite = compute_composite_score(dim_scores, profile=weight_profile)
    indicators = collect_indicators(responses)

    return {
        "dimension_scores": dim_scores,
        "composite": composite,
        "indicators": indicators,
    }
