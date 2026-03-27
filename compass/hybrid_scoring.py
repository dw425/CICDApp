"""Hybrid scoring: 70/30 telemetry/assessment blend with confidence and discrepancy detection.
# ****Truth Agent Verified**** — compute_hybrid_score (70/30 blend, 4 confidence levels,
# discrepancy flag >20pts), compute_hybrid_composite (weighted geometric mean)
"""

import math
from compass.scoring_constants import score_to_tier, TIER_COLORS


def compute_hybrid_score(telemetry_score, assessment_score):
    """Blend telemetry and assessment scores.

    Rules:
      Both exist: telemetry * 0.70 + assessment * 0.30
      Only telemetry: telemetry * 1.0 (confidence: medium)
      Only assessment: assessment * 1.0 (confidence: low)
      Neither: 0 (confidence: none)
    """
    flag = None

    if telemetry_score is not None and assessment_score is not None:
        blended = telemetry_score * 0.70 + assessment_score * 0.30
        confidence = "high"
        discrepancy = abs(telemetry_score - assessment_score)
        if discrepancy > 20:
            flag = {
                "type": "discrepancy",
                "message": f"Self-reported {assessment_score:.0f} but telemetry measured {telemetry_score:.0f}",
                "telemetry_score": telemetry_score,
                "assessment_score": assessment_score,
                "delta": round(telemetry_score - assessment_score, 1),
            }
    elif telemetry_score is not None:
        blended = telemetry_score
        confidence = "medium"
    elif assessment_score is not None:
        blended = assessment_score
        confidence = "low"
        flag = {
            "type": "no_telemetry",
            "message": "Score based on self-assessment only. Connect a data source for objective measurement.",
        }
    else:
        blended = 0
        confidence = "none"
        flag = {"type": "no_data", "message": "No data available for this dimension."}

    return {
        "score": round(blended, 2),
        "confidence": confidence,
        "telemetry_score": telemetry_score,
        "assessment_score": assessment_score,
        "flag": flag,
    }


def compute_hybrid_composite(dimension_hybrid_scores: dict, weight_profile: dict) -> dict:
    """Compute overall composite from hybrid dimension scores using weighted geometric mean."""
    log_sum = 0.0
    weight_sum = 0.0
    breakdown = {}

    for dim, score_data in dimension_hybrid_scores.items():
        if "." in dim:
            continue

        score = score_data.get("score", 0)
        weight = weight_profile.get(dim, 0)

        if weight > 0 and score is not None and score >= 0:
            log_sum += weight * math.log(score + 1)
            weight_sum += weight

        level, label = score_to_tier(score)
        breakdown[dim] = {
            "score": score,
            "level": level,
            "label": label,
            "color": TIER_COLORS[level],
            "weight": weight,
            "confidence": score_data.get("confidence", "none"),
            "flag": score_data.get("flag"),
        }

    composite = math.exp(log_sum / weight_sum) - 1 if weight_sum > 0 else 0
    composite = round(min(max(composite, 0), 100), 2)
    overall_level, overall_label = score_to_tier(composite)

    return {
        "overall_score": composite,
        "overall_level": overall_level,
        "overall_label": overall_label,
        "overall_color": TIER_COLORS[overall_level],
        "dimension_breakdown": breakdown,
    }
