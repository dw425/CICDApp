"""Generate 5 sample assessments with realistic responses for demo/testing."""

import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compass.assessment_store import (
    create_organization,
    create_assessment,
    save_responses_batch,
    save_scores,
    get_all_organizations,
    get_all_assessments,
    _write_json,
    _ORGS_FILE,
    _ASSESSMENTS_FILE,
)
from compass.scoring_engine import (
    full_score_assessment,
    score_all_dimensions,
    compute_composite_score,
    collect_indicators,
)
from compass.question_bank.loader import (
    load_all_dimensions,
    get_all_questions,
    get_core_dimensions,
)
from compass.roadmap_engine import generate_roadmap
from compass.antipattern_engine import detect_anti_patterns


# ── Organization profiles ──
ORG_PROFILES = [
    {
        "name": "Acme Financial Services",
        "industry": "Financial Services",
        "size": "enterprise",
        "cloud_provider": "Azure",
        "uses_databricks": True,
        "weight_profile": "financial_services",
        "respondent_name": "Sarah Chen",
        "respondent_role": "VP of Platform Engineering",
        "score_band": "high",  # 70-90
    },
    {
        "name": "TechStart AI",
        "industry": "Technology",
        "size": "startup",
        "cloud_provider": "AWS",
        "uses_databricks": True,
        "weight_profile": "startup",
        "respondent_name": "Mike Rodriguez",
        "respondent_role": "CTO",
        "score_band": "elite",  # 80-95
    },
    {
        "name": "MedData Corp",
        "industry": "Healthcare",
        "size": "mid_market",
        "cloud_provider": "Azure",
        "uses_databricks": True,
        "weight_profile": "balanced",
        "respondent_name": "Dr. Priya Sharma",
        "respondent_role": "Director of Data Engineering",
        "score_band": "mid",  # 40-65
    },
    {
        "name": "GovCloud Agency",
        "industry": "Government",
        "size": "enterprise",
        "cloud_provider": "Azure",
        "uses_databricks": True,
        "weight_profile": "federal_government",
        "respondent_name": "James Wilson",
        "respondent_role": "Chief Data Officer",
        "score_band": "low",  # 20-45
    },
    {
        "name": "DataPipe Analytics",
        "industry": "Technology",
        "size": "mid_market",
        "cloud_provider": "GCP",
        "uses_databricks": True,
        "weight_profile": "data_engineering",
        "respondent_name": "Lisa Park",
        "respondent_role": "Lead DevOps Engineer",
        "score_band": "high_mid",  # 55-75
    },
]

# Score bands → response value ranges
SCORE_BANDS = {
    "elite": (4, 5),
    "high": (3, 5),
    "high_mid": (3, 4),
    "mid": (2, 4),
    "low": (1, 3),
}


def generate_response(question: dict, score_band: str) -> dict:
    """Generate a realistic response for a question based on score band."""
    qtype = question.get("type", "likert")
    lo, hi = SCORE_BANDS[score_band]

    if qtype in ("likert", "single_select"):
        options = question.get("options", [])
        valid = [o for o in options if o.get("value", 0) != -1]
        if not valid:
            return {"value": 1}
        values = [o["value"] for o in valid]
        min_v, max_v = min(values), max(values)
        # Map score band to value range
        target_lo = min_v + (max_v - min_v) * (lo - 1) / 4
        target_hi = min_v + (max_v - min_v) * (hi - 1) / 4
        # Pick a value in range
        candidates = [v for v in values if target_lo <= v <= target_hi]
        if not candidates:
            candidates = [min(values, key=lambda v: abs(v - (target_lo + target_hi) / 2))]
        return {"value": random.choice(candidates)}

    elif qtype == "binary":
        # Higher bands more likely to say True
        prob = (lo + hi) / 10
        return {"value": random.random() < prob}

    elif qtype == "multi_select":
        options = question.get("options", [])
        valid = [o for o in options if o.get("value") not in ("none", -1)]
        n_select = max(1, int(len(valid) * (lo + hi) / 10))
        n_select = min(n_select, len(valid))
        selected = random.sample(valid, n_select)
        return {"values": [o["value"] for o in selected]}

    elif qtype == "freeform":
        return {"text": "Implementing improvements this quarter."}

    return {"value": 1}


def main():
    random.seed(42)

    # Clear existing data
    print("Clearing existing assessment data...")
    _write_json(_ORGS_FILE, [])
    _write_json(_ASSESSMENTS_FILE, [])

    # Load questions
    load_all_dimensions()
    all_questions = get_all_questions()
    core_dims = get_core_dimensions()
    core_question_ids = set()
    for dim in core_dims:
        for q in dim.get("questions", []):
            core_question_ids.add(q["id"])

    print(f"Loaded {len(all_questions)} questions across {len(core_dims)} core dimensions\n")

    for i, profile in enumerate(ORG_PROFILES, 1):
        print(f"{'='*60}")
        print(f"Assessment {i}/5: {profile['name']}")
        print(f"  Industry: {profile['industry']} | Size: {profile['size']}")
        print(f"  Respondent: {profile['respondent_name']} ({profile['respondent_role']})")
        print(f"  Score Band: {profile['score_band']}")

        # Create org
        org = create_organization(
            name=profile["name"],
            industry=profile["industry"],
            size=profile["size"],
            cloud_provider=profile["cloud_provider"],
            uses_databricks=profile["uses_databricks"],
        )
        print(f"  Org ID: {org['id']}")

        # Create assessment
        assessment = create_assessment(
            org_id=org["id"],
            assessment_type="full",
            weight_profile=profile["weight_profile"],
            respondent_name=profile["respondent_name"],
            respondent_role=profile["respondent_role"],
        )
        print(f"  Assessment ID: {assessment['id']}")

        # Generate responses for core questions
        responses_batch = []
        responses_dict = {}
        for q in all_questions:
            if q["id"] not in core_question_ids:
                continue
            resp_val = generate_response(q, profile["score_band"])
            responses_batch.append({
                "question_id": q["id"],
                "dimension": q.get("_dimension", ""),
                "sub_dimension": q.get("_sub_dimension"),
                "response_type": q.get("type", "likert"),
                "response_value": resp_val,
            })
            responses_dict[q["id"]] = {
                "response_type": q.get("type", "likert"),
                "response_value": resp_val,
            }

        save_responses_batch(assessment["id"], responses_batch)
        print(f"  Saved {len(responses_batch)} responses")

        # Score the assessment
        result = full_score_assessment(
            responses_dict,
            weight_profile=profile["weight_profile"],
            uses_databricks=False,
        )

        dim_scores = result["dimension_scores"]
        composite = result["composite"]

        # Anti-patterns
        try:
            indicators = result.get("indicators", set())
            anti_patterns = detect_anti_patterns(indicators)
        except Exception:
            anti_patterns = []

        # Roadmap
        try:
            roadmap = generate_roadmap(dim_scores, composite)
        except Exception:
            roadmap = {"recommendations": [], "gaps": []}

        # Save scores
        save_scores(
            assessment["id"],
            dim_scores,
            composite,
            anti_patterns,
            roadmap,
        )

        print(f"  Composite Score: {composite['overall_score']:.1f} "
              f"(L{composite['overall_level']} - {composite['overall_label']})")
        print(f"  Weight Profile: {profile['weight_profile']}")
        print(f"  Dimension Scores:")
        for dim_id, data in sorted(dim_scores.items()):
            if isinstance(data, dict):
                print(f"    {data.get('display_name', dim_id):30s} "
                      f"{data.get('raw_score', 0):5.1f}  "
                      f"L{data.get('level', 0)} {data.get('label', '')}")
        print()

    # Summary
    orgs = get_all_organizations()
    assessments = get_all_assessments()
    completed = [a for a in assessments if a.get("status") == "completed"]

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Organizations created: {len(orgs)}")
    print(f"Assessments created:   {len(assessments)}")
    print(f"Completed:             {len(completed)}")
    print(f"\nAssessment store files:")
    print(f"  {_ORGS_FILE}")
    print(f"  {_ASSESSMENTS_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
