"""ROI Calculator — Quantifies business value of CI/CD maturity improvements.

Uses industry benchmarks from DORA 2024, McKinsey DVI, Forrester TEI, and
CodeScene to estimate developer hours saved, incident cost reduction,
deployment velocity gains, and compliance risk reduction.
"""

import math


# Industry benchmarks
BENCHMARKS = {
    "avg_engineer_hourly_cost": 85.0,  # USD, loaded cost
    "avg_incident_cost": 5600.0,  # USD per incident (PagerDuty State of Digital Ops)
    "elite_deploy_freq_multiplier": 182,  # DORA 2024: elite vs low
    "elite_recovery_multiplier": 2293,  # DORA 2024
    "automation_remediation_reduction": 0.80,  # Forrester TEI: 75-90% reduction
    "top_dvi_revenue_multiplier": 4.5,  # McKinsey: 4-5x revenue growth
    "tech_debt_commit_ratio": 0.14,  # CodeScene: 2-3% code gets 11-16% of commits
}


def compute_roi(
    before_scores: dict,
    after_scores: dict,
    org_context: dict,
) -> dict:
    """
    Compute ROI from maturity improvements.

    Args:
        before_scores: {dimension: score (0-100)} before improvements
        after_scores: {dimension: score (0-100)} after improvements
        org_context: {
            "engineer_count": int,
            "avg_salary": float (annual),
            "deploy_frequency_per_week": float,
            "avg_build_time_minutes": float,
            "builds_per_day": int,
            "incidents_per_month": float,
            "avg_mttr_hours": float,
        }

    Returns: {
        "developer_hours_saved_annually": float,
        "incident_cost_reduction_annually": float,
        "deployment_velocity_gain_pct": float,
        "compliance_risk_reduction_pct": float,
        "total_annual_value": float,
        "breakdown": [...],
    }
    """
    engineers = org_context.get("engineer_count", 50)
    salary = org_context.get("avg_salary", 170000)
    hourly = salary / 2080  # 40hr/wk × 52wk
    deploy_freq = org_context.get("deploy_frequency_per_week", 3)
    build_time = org_context.get("avg_build_time_minutes", 15)
    builds_day = org_context.get("builds_per_day", 10)
    incidents_month = org_context.get("incidents_per_month", 4)
    mttr_hours = org_context.get("avg_mttr_hours", 4)

    # Calculate score deltas
    before_avg = sum(before_scores.values()) / max(len(before_scores), 1)
    after_avg = sum(after_scores.values()) / max(len(after_scores), 1)
    improvement_pct = (after_avg - before_avg) / max(before_avg, 1) * 100

    breakdown = []

    # 1. Build time savings
    build_improvement = _score_delta(before_scores, after_scores, "build_integration")
    build_time_reduction_pct = min(build_improvement * 0.5, 50)  # Cap at 50% reduction
    minutes_saved_per_build = build_time * (build_time_reduction_pct / 100)
    annual_build_hours_saved = (minutes_saved_per_build * builds_day * 260) / 60
    build_savings = annual_build_hours_saved * hourly * engineers * 0.3  # Not all engineers build all day
    breakdown.append({
        "category": "Build Time Savings",
        "description": f"{build_time_reduction_pct:.0f}% faster builds saving {annual_build_hours_saved:.0f} hours/year",
        "annual_value": round(build_savings),
    })

    # 2. Incident cost reduction
    reliability_improvement = _score_delta(before_scores, after_scores, "pipeline_reliability")
    incident_reduction_pct = min(reliability_improvement * 0.4, 40)
    incidents_prevented = incidents_month * 12 * (incident_reduction_pct / 100)
    incident_savings = incidents_prevented * BENCHMARKS["avg_incident_cost"]
    breakdown.append({
        "category": "Incident Cost Reduction",
        "description": f"{incidents_prevented:.0f} fewer incidents/year at ${BENCHMARKS['avg_incident_cost']:,.0f} each",
        "annual_value": round(incident_savings),
    })

    # 3. MTTR improvement
    mttr_improvement = _score_delta(before_scores, after_scores, "observability")
    mttr_reduction_pct = min(mttr_improvement * 0.3, 30)
    mttr_hours_saved = mttr_hours * (mttr_reduction_pct / 100) * incidents_month * 12
    mttr_team_hours = mttr_hours_saved * 3  # Avg 3 engineers per incident
    mttr_savings = mttr_team_hours * hourly
    breakdown.append({
        "category": "Faster Incident Recovery",
        "description": f"{mttr_reduction_pct:.0f}% faster MTTR saving {mttr_team_hours:.0f} team-hours/year",
        "annual_value": round(mttr_savings),
    })

    # 4. Deployment velocity gain
    deploy_improvement = _score_delta(before_scores, after_scores, "deployment_release")
    velocity_gain_pct = min(deploy_improvement * 0.6, 60)
    new_deploy_freq = deploy_freq * (1 + velocity_gain_pct / 100)
    breakdown.append({
        "category": "Deployment Velocity",
        "description": f"Deploy frequency: {deploy_freq:.1f}/wk → {new_deploy_freq:.1f}/wk ({velocity_gain_pct:.0f}% increase)",
        "annual_value": 0,  # Indirect value, not dollar-quantified
    })

    # 5. Compliance risk reduction
    security_improvement = _score_delta(before_scores, after_scores, "security_compliance")
    compliance_reduction = min(security_improvement * 0.5, 50)
    # Estimated cost of compliance failure (audit findings, remediation sprints)
    compliance_savings = compliance_reduction / 100 * 50000  # $50k baseline risk
    breakdown.append({
        "category": "Compliance Risk Reduction",
        "description": f"{compliance_reduction:.0f}% reduction in compliance exposure",
        "annual_value": round(compliance_savings),
    })

    # 6. Developer toil reduction
    dx_improvement = _score_delta(before_scores, after_scores, "developer_experience")
    toil_reduction_pct = min(dx_improvement * 0.3, 30)
    toil_hours_saved = engineers * 2 * 52 * (toil_reduction_pct / 100)  # 2hr/wk avg toil
    toil_savings = toil_hours_saved * hourly
    breakdown.append({
        "category": "Developer Toil Reduction",
        "description": f"{toil_reduction_pct:.0f}% less toil, {toil_hours_saved:.0f} hours/year recovered",
        "annual_value": round(toil_savings),
    })

    total = sum(b["annual_value"] for b in breakdown)

    return {
        "developer_hours_saved_annually": round(annual_build_hours_saved + mttr_team_hours + toil_hours_saved),
        "incident_cost_reduction_annually": round(incident_savings),
        "deployment_velocity_gain_pct": round(velocity_gain_pct, 1),
        "compliance_risk_reduction_pct": round(compliance_reduction, 1),
        "total_annual_value": round(total),
        "improvement_pct": round(improvement_pct, 1),
        "before_avg": round(before_avg, 1),
        "after_avg": round(after_avg, 1),
        "breakdown": breakdown,
    }


def _score_delta(before: dict, after: dict, dimension: str) -> float:
    """Get the score improvement for a dimension (0-100 scale)."""
    b = before.get(dimension, 0)
    a = after.get(dimension, b)
    return max(0, a - b)
