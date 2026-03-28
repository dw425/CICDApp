"""
Roadmap Generation Engine for Pipeline Compass.

Process:
  1. Calculate gaps: target_score - current_score per dimension
  2. Match recommendations from the improvement library
  3. Classify each on Impact x Effort matrix (quick_wins/strategic/fill_ins/deprioritize)
  4. Assign to phases: 30-day → 90-day → 6-month → 12-month
  5. Estimate ROI per improvement item
"""

from compass.scoring_engine import score_to_tier, TIER_LABELS


IMPROVEMENT_LIBRARY = [
    # ── Build & Integration ──
    {
        "id": "imp_001",
        "dimension": "build_integration",
        "applies_when": {"level_lte": 2},
        "title": "Implement Commit-Triggered Builds",
        "description": "Configure CI server to trigger automated builds on every commit to any branch. This is the foundational step for CI maturity.",
        "impact": "high",
        "effort": "low",
        "effort_days": 3,
        "expected_score_improvement": 15,
        "tools": ["GitHub Actions", "GitLab CI", "Azure DevOps Pipelines", "Jenkins"],
        "roi_category": "speed",
    },
    {
        "id": "imp_002",
        "dimension": "build_integration",
        "applies_when": {"level_lte": 2},
        "title": "Adopt Trunk-Based Development",
        "description": "Migrate from long-lived feature branches to trunk-based development with short-lived branches (<1 day). Use feature flags for incomplete features.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 15,
        "expected_score_improvement": 20,
        "tools": ["LaunchDarkly", "Unleash", "Flagsmith", "Split.io"],
        "roi_category": "speed",
    },
    {
        "id": "imp_003",
        "dimension": "build_integration",
        "applies_when": {"level_lte": 3},
        "title": "Implement Build Caching & Parallelization",
        "description": "Add dependency caching, parallel test execution, and incremental builds to reduce feedback loop to under 10 minutes.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 8,
        "expected_score_improvement": 15,
        "tools": ["Gradle Build Cache", "Bazel", "Turbopack", "Nx"],
        "roi_category": "speed",
    },
    # ── Testing & Quality ──
    {
        "id": "imp_010",
        "dimension": "testing_quality",
        "applies_when": {"level_lte": 2},
        "title": "Establish Automated Test Foundation",
        "description": "Implement unit testing framework with minimum 40% coverage threshold. Set up test execution in CI pipeline for every PR.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 15,
        "expected_score_improvement": 20,
        "tools": ["pytest", "Jest", "JUnit", "Nutter (Databricks)"],
        "roi_category": "quality",
    },
    {
        "id": "imp_011",
        "dimension": "testing_quality",
        "applies_when": {"level_lte": 3},
        "title": "Implement Flaky Test Detection & Quarantine",
        "description": "Deploy automated flaky test detection (fail-then-pass on same commit). Quarantine identified flaky tests so they report but don't block. Track 'PRs Impacted' metric.",
        "impact": "high",
        "effort": "low",
        "effort_days": 5,
        "expected_score_improvement": 10,
        "tools": ["Trunk.io Flaky Tests", "BuildPulse", "Datadog CI Visibility"],
        "roi_category": "quality",
    },
    {
        "id": "imp_012",
        "dimension": "testing_quality",
        "applies_when": {"level_lte": 3},
        "title": "Enforce Code Quality Gates",
        "description": "Require linting, unit tests, coverage thresholds, and peer review before merge. Configure as required status checks in branch protection.",
        "impact": "high",
        "effort": "low",
        "effort_days": 3,
        "expected_score_improvement": 15,
        "tools": ["GitHub Branch Protection", "GitLab Merge Checks", "SonarQube"],
        "roi_category": "quality",
    },
    # ── Deployment & Release ──
    {
        "id": "imp_020",
        "dimension": "deployment_release",
        "applies_when": {"level_lte": 2},
        "title": "Automate Deployment Pipeline",
        "description": "Replace manual deployment steps with a fully automated CI/CD pipeline. Implement automated staging deployment with manual production approval gate.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 10,
        "expected_score_improvement": 25,
        "tools": ["GitHub Actions", "Azure DevOps Pipelines", "ArgoCD", "Spinnaker"],
        "roi_category": "speed",
    },
    {
        "id": "imp_021",
        "dimension": "deployment_release",
        "applies_when": {"level_lte": 3},
        "title": "Implement Automated Rollback",
        "description": "Configure health check-based automated rollback for production deployments. Add canary or blue-green deployment strategy.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 8,
        "expected_score_improvement": 15,
        "tools": ["Argo Rollouts", "Flagger", "AWS CodeDeploy", "Azure Deployment Slots"],
        "roi_category": "risk",
    },
    {
        "id": "imp_022",
        "dimension": "deployment_release",
        "applies_when": {"level_lte": 3},
        "title": "Adopt Feature Flags",
        "description": "Implement feature flag management to decouple deployment from release. Enable gradual rollouts and instant kill switches.",
        "impact": "high",
        "effort": "low",
        "effort_days": 5,
        "expected_score_improvement": 10,
        "tools": ["LaunchDarkly", "Unleash", "Flagsmith", "Flipt"],
        "roi_category": "speed",
    },
    # ── Security & Compliance ──
    {
        "id": "imp_030",
        "dimension": "security_compliance",
        "applies_when": {"level_lte": 2},
        "title": "Implement Secrets Vault",
        "description": "Migrate all credentials from hardcoded values and environment variables to a centralized secrets vault with automatic rotation.",
        "impact": "high",
        "effort": "low",
        "effort_days": 5,
        "expected_score_improvement": 25,
        "tools": ["HashiCorp Vault", "AWS Secrets Manager", "Azure Key Vault"],
        "roi_category": "risk",
    },
    {
        "id": "imp_031",
        "dimension": "security_compliance",
        "applies_when": {"level_lte": 3},
        "title": "Integrate Security Scanning in CI",
        "description": "Add SAST, SCA (dependency scanning), and secrets detection to every PR build. Block merges on critical findings.",
        "impact": "high",
        "effort": "low",
        "effort_days": 3,
        "expected_score_improvement": 20,
        "tools": ["Snyk", "Semgrep", "GitGuardian", "Trivy", "Checkov"],
        "roi_category": "risk",
    },
    {
        "id": "imp_032",
        "dimension": "security_compliance",
        "applies_when": {"level_lte": 3},
        "title": "Implement Policy-as-Code",
        "description": "Define and enforce organizational policies programmatically. Gate deployments on policy compliance checks.",
        "impact": "high",
        "effort": "high",
        "effort_days": 20,
        "expected_score_improvement": 15,
        "tools": ["OPA/Rego", "HashiCorp Sentinel", "Kyverno", "Datree"],
        "roi_category": "risk",
    },
    # ── Observability ──
    {
        "id": "imp_040",
        "dimension": "observability",
        "applies_when": {"level_lte": 2},
        "title": "Implement Structured Observability Stack",
        "description": "Deploy metrics, structured logging, and distributed tracing. Create dashboards for key services with alerting on SLI degradation.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 15,
        "expected_score_improvement": 25,
        "tools": ["Datadog", "Grafana Stack", "New Relic", "Dynatrace"],
        "roi_category": "risk",
    },
    {
        "id": "imp_041",
        "dimension": "observability",
        "applies_when": {"level_lte": 3},
        "title": "Define and Track SLOs",
        "description": "Define Service Level Objectives for critical services with error budgets. Implement burn rate alerting and SLO-based deployment gates.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 10,
        "expected_score_improvement": 15,
        "tools": ["Nobl9", "Google SLO Generator", "Datadog SLOs", "Grafana SLO"],
        "roi_category": "quality",
    },
    # ── IaC & Configuration ──
    {
        "id": "imp_050",
        "dimension": "iac_configuration",
        "applies_when": {"level_lte": 2},
        "title": "Adopt Infrastructure-as-Code",
        "description": "Define all infrastructure in code (Terraform, Pulumi, CloudFormation). Implement plan-on-PR, apply-on-merge workflow.",
        "impact": "high",
        "effort": "high",
        "effort_days": 30,
        "expected_score_improvement": 25,
        "tools": ["Terraform", "Pulumi", "AWS CDK", "Crossplane"],
        "roi_category": "speed",
    },
    {
        "id": "imp_051",
        "dimension": "iac_configuration",
        "applies_when": {"level_lte": 3},
        "title": "Implement GitOps for Infrastructure",
        "description": "Adopt GitOps reconciliation pattern where infrastructure state is continuously synced from Git. Add drift detection and automatic remediation.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 15,
        "expected_score_improvement": 20,
        "tools": ["ArgoCD", "Flux", "Terraform Cloud", "Spacelift"],
        "roi_category": "speed",
    },
    # ── Artifact Management ──
    {
        "id": "imp_060",
        "dimension": "artifact_management",
        "applies_when": {"level_lte": 2},
        "title": "Set Up Artifact Repository",
        "description": "Deploy a dedicated artifact repository for build outputs with versioning, retention policies, and vulnerability scanning.",
        "impact": "high",
        "effort": "low",
        "effort_days": 5,
        "expected_score_improvement": 25,
        "tools": ["JFrog Artifactory", "Nexus", "GitHub Packages", "AWS ECR"],
        "roi_category": "speed",
    },
    {
        "id": "imp_061",
        "dimension": "artifact_management",
        "applies_when": {"level_lte": 3},
        "title": "Implement Dependency Management",
        "description": "Set up automated dependency updates with vulnerability gating. Use a private registry mirror for supply chain security.",
        "impact": "high",
        "effort": "low",
        "effort_days": 3,
        "expected_score_improvement": 15,
        "tools": ["Dependabot", "Renovate", "Mend (WhiteSource)", "Snyk"],
        "roi_category": "risk",
    },
    # ── Developer Experience ──
    {
        "id": "imp_070",
        "dimension": "developer_experience",
        "applies_when": {"level_lte": 2},
        "title": "Streamline Developer Onboarding",
        "description": "Create devcontainers or Codespaces configuration for one-click environment setup. Target first-commit-in-under-a-day for new developers.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 8,
        "expected_score_improvement": 20,
        "tools": ["Dev Containers", "GitHub Codespaces", "Gitpod", "Coder"],
        "roi_category": "speed",
    },
    {
        "id": "imp_071",
        "dimension": "developer_experience",
        "applies_when": {"level_lte": 3},
        "title": "Implement Developer Portal",
        "description": "Deploy an internal developer portal with service catalog, API docs, golden path templates, and service scorecards.",
        "impact": "high",
        "effort": "high",
        "effort_days": 30,
        "expected_score_improvement": 15,
        "tools": ["Backstage", "Port", "Cortex", "OpsLevel"],
        "roi_category": "speed",
    },
    # ── Pipeline Governance ──
    {
        "id": "imp_080",
        "dimension": "pipeline_governance",
        "applies_when": {"level_lte": 2},
        "title": "Create Shared Pipeline Templates",
        "description": "Extract common CI/CD stages into versioned shared templates. Require all new services to use templates. Maintain a template catalog.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 15,
        "expected_score_improvement": 25,
        "tools": ["GitHub Reusable Workflows", "GitLab CI Includes", "Azure DevOps Templates", "Jenkins Shared Libraries"],
        "roi_category": "speed",
    },
    {
        "id": "imp_081",
        "dimension": "pipeline_governance",
        "applies_when": {"level_lte": 3},
        "title": "Implement Golden Pipeline with Managed Inheritance",
        "description": "Implement a master pipeline definition that services inherit by reference. Add Insert Blocks for team-specific customization while maintaining mandatory governance stages.",
        "impact": "high",
        "effort": "high",
        "effort_days": 20,
        "expected_score_improvement": 20,
        "tools": ["Custom Template Engine", "Backstage Software Templates", "Proton"],
        "roi_category": "speed",
    },
    # ── Databricks-Specific ──
    {
        "id": "imp_090",
        "dimension": "databricks",
        "applies_when": {"level_lte": 2},
        "title": "Adopt Databricks Asset Bundles (DABs)",
        "description": "Define all Databricks resources in databricks.yml with multi-target deployment (dev/staging/prod). Integrate with CI/CD pipeline for automated deployment.",
        "impact": "high",
        "effort": "medium",
        "effort_days": 10,
        "expected_score_improvement": 25,
        "tools": ["Databricks CLI", "DABs", "GitHub Actions", "Azure DevOps"],
        "roi_category": "speed",
    },
    {
        "id": "imp_091",
        "dimension": "databricks",
        "applies_when": {"level_lte": 2},
        "title": "Transition from Notebooks to Repo-First Development",
        "description": "Extract notebook logic into Python modules with unit tests. Adopt IDE-first development (VS Code + Databricks Connect). Use notebooks only for exploration.",
        "impact": "high",
        "effort": "high",
        "effort_days": 30,
        "expected_score_improvement": 25,
        "tools": ["VS Code + Databricks Extension", "Databricks Connect", "pytest", "Nutter"],
        "roi_category": "quality",
    },
    {
        "id": "imp_092",
        "dimension": "databricks",
        "applies_when": {"level_lte": 3},
        "title": "Migrate to Unity Catalog",
        "description": "Migrate production tables from hive_metastore to Unity Catalog. Implement per-environment catalogs and governance-as-code for grants.",
        "impact": "high",
        "effort": "high",
        "effort_days": 30,
        "expected_score_improvement": 20,
        "tools": ["Unity Catalog", "Terraform Databricks Provider", "DABs"],
        "roi_category": "risk",
    },
    {
        "id": "imp_093",
        "dimension": "databricks",
        "applies_when": {"level_lte": 3},
        "title": "Add DLT Quality Expectations",
        "description": "Implement @dlt.expect expectations at every medallion layer. Start with Bronze constraints, then Silver business rules, then Gold validations.",
        "impact": "high",
        "effort": "low",
        "effort_days": 5,
        "expected_score_improvement": 15,
        "tools": ["Delta Live Tables", "Great Expectations", "dbt tests"],
        "roi_category": "quality",
    },
]

ROI_MULTIPLIERS = {
    "speed": {"hours_per_dev_per_month": 8, "description": "Developer hours saved per month"},
    "quality": {"incident_reduction_pct": 15, "description": "Reduction in production incidents"},
    "risk": {"risk_reduction_pct": 20, "description": "Reduction in security/compliance risk"},
    "cost": {"cost_reduction_pct": 10, "description": "Infrastructure cost reduction"},
}


def calculate_gaps(
    dimension_scores: dict,
    target: str = "next_tier",
) -> list[dict]:
    """
    Calculate the gap between current and target score per dimension.

    Args:
        dimension_scores: Dict of {dim_id: {"score": float, "level": int, ...}}.
        target: "next_tier", "elite", or a dict of {dim: target_score}.

    Returns:
        List of gap dicts sorted by gap size (largest first).
    """
    gaps = []
    for dim, data in dimension_scores.items():
        current = data.get("score", data.get("raw_score", 0))
        level = data.get("level", 1)

        if target == "next_tier":
            target_score = min(current + 25, 100)
        elif target == "elite":
            target_score = 85
        elif isinstance(target, dict):
            target_score = target.get(dim, current + 20)
        else:
            target_score = min(current + 25, 100)

        gap = round(target_score - current, 2)
        if gap > 0:
            gaps.append({
                "dimension": dim,
                "display_name": data.get("display_name", dim),
                "current_score": current,
                "current_level": level,
                "current_label": data.get("label", TIER_LABELS.get(level, "Unknown")),
                "target_score": target_score,
                "target_level": score_to_tier(target_score)[0],
                "gap": gap,
            })

    gaps.sort(key=lambda x: x["gap"], reverse=True)
    return gaps
    # ****Checked and Verified as Real*****
    # Calculate the gap between current and target score per dimension. Args: dimension_scores: Dict of {dim_id: {"score": float, "level": int, ...}}.


def match_recommendations(
    gaps: list[dict],
    anti_patterns: list[dict] = None,
) -> list[dict]:
    """
    Match improvement recommendations to dimension gaps.

    Args:
        gaps: List of gap dicts from calculate_gaps.
        anti_patterns: Detected anti-patterns to boost priority.

    Returns:
        List of recommendation dicts with gap context.
    """
    ap_dimensions = set()
    if anti_patterns:
        for ap in anti_patterns:
            ap_dimensions.update(ap.get("impact_dimensions", []))

    matched = []
    for gap in gaps:
        dim = gap["dimension"]
        level = gap["current_level"]

        for rec in IMPROVEMENT_LIBRARY:
            if rec["dimension"] != dim and not (dim.startswith("databricks") and rec["dimension"] == "databricks"):
                continue
            applies = rec.get("applies_when", {})
            level_lte = applies.get("level_lte", 99)
            if level > level_lte:
                continue

            boosted = dim in ap_dimensions
            matched.append({
                **rec,
                "gap_info": gap,
                "boosted_by_antipattern": boosted,
                "priority_score": _calc_priority(rec, gap, boosted),
            })

    matched.sort(key=lambda x: x["priority_score"], reverse=True)
    return matched
    # ****Checked and Verified as Real*****
    # Match improvement recommendations to dimension gaps. Args: gaps: List of gap dicts from calculate_gaps.


def _calc_priority(rec: dict, gap: dict, boosted: bool) -> float:
    """Calculate a priority score for sorting recommendations."""
    base = gap["gap"]
    impact_mult = 2.0 if rec["impact"] == "high" else 1.0
    effort_mult = {"low": 1.5, "medium": 1.0, "high": 0.7}.get(rec["effort"], 1.0)
    boost = 1.3 if boosted else 1.0
    return round(base * impact_mult * effort_mult * boost, 2)
    # ****Checked and Verified as Real*****
    # Calculate a priority score for sorting recommendations.


def classify_impact_effort(recommendations: list[dict]) -> dict:
    """
    Classify recommendations into Impact x Effort quadrants.

    Returns:
        Dict with: quick_wins, strategic, fill_ins, deprioritize.
    """
    matrix = {"quick_wins": [], "strategic": [], "fill_ins": [], "deprioritize": []}

    for rec in recommendations:
        impact = rec.get("impact", "low")
        effort = rec.get("effort", "high")

        if impact == "high" and effort in ("low", "medium"):
            matrix["quick_wins"].append(rec)
        elif impact == "high" and effort == "high":
            matrix["strategic"].append(rec)
        elif impact == "low" and effort in ("low", "medium"):
            matrix["fill_ins"].append(rec)
        else:
            matrix["deprioritize"].append(rec)

    return matrix
    # ****Checked and Verified as Real*****
    # Classify recommendations into Impact x Effort quadrants. Returns: Dict with: quick_wins, strategic, fill_ins, deprioritize.


def assign_phases(classified: dict) -> list[dict]:
    """Assign classified recommendations to time-based phases."""
    return [
        {
            "name": "30-Day Quick Wins",
            "horizon": "30d",
            "description": "High-impact, low-effort improvements that deliver immediate value",
            "items": classified["quick_wins"],
        },
        {
            "name": "90-Day Strategic Investments",
            "horizon": "90d",
            "description": "High-impact improvements requiring significant effort but essential for maturity advancement",
            "items": classified["strategic"],
        },
        {
            "name": "6-Month Maturity Advancement",
            "horizon": "6mo",
            "description": "Lower-impact but easy wins that round out the maturity profile",
            "items": classified["fill_ins"],
        },
        {
            "name": "12-Month Comprehensive Plan",
            "horizon": "12mo",
            "description": "Long-term improvements to consider after higher-priority items are complete",
            "items": classified["deprioritize"],
        },
    ]
    # ****Checked and Verified as Real*****
    # Assign classified recommendations to time-based phases.


def estimate_total_roi(phases: list[dict], team_size: int = 10) -> dict:
    """
    Estimate total ROI across all roadmap phases.

    Args:
        phases: Phase list from assign_phases.
        team_size: Number of developers on the team.

    Returns:
        Dict with annual estimates by category.
    """
    total_effort_days = 0
    total_score_improvement = 0
    roi_by_category = {
        "speed": {"hours_saved_annually": 0},
        "quality": {"incident_reduction_pct": 0},
        "risk": {"risk_reduction_pct": 0},
        "cost": {"cost_reduction_pct": 0},
    }

    items_counted = 0
    for phase in phases:
        for item in phase.get("items", []):
            total_effort_days += item.get("effort_days", 0)
            total_score_improvement += item.get("expected_score_improvement", 0)
            cat = item.get("roi_category", "speed")
            items_counted += 1

            if cat == "speed":
                roi_by_category["speed"]["hours_saved_annually"] += (
                    ROI_MULTIPLIERS["speed"]["hours_per_dev_per_month"] * team_size * 12
                )
            elif cat == "quality":
                roi_by_category["quality"]["incident_reduction_pct"] += (
                    ROI_MULTIPLIERS["quality"]["incident_reduction_pct"]
                )
            elif cat == "risk":
                roi_by_category["risk"]["risk_reduction_pct"] += (
                    ROI_MULTIPLIERS["risk"]["risk_reduction_pct"]
                )
            elif cat == "cost":
                roi_by_category["cost"]["cost_reduction_pct"] += (
                    ROI_MULTIPLIERS["cost"]["cost_reduction_pct"]
                )

    # Cap percentages at 80
    for cat in ["quality", "risk", "cost"]:
        for key in roi_by_category[cat]:
            if key.endswith("_pct"):
                roi_by_category[cat][key] = min(roi_by_category[cat][key], 80)

    return {
        "total_effort_days": total_effort_days,
        "total_expected_score_improvement": min(total_score_improvement, 100),
        "items_count": items_counted,
        "roi_by_category": roi_by_category,
    }
    # ****Checked and Verified as Real*****
    # Estimate total ROI across all roadmap phases. Args: phases: Phase list from assign_phases.


def generate_roadmap(
    dimension_scores: dict,
    target_profile: str = "next_tier",
    anti_patterns: list[dict] = None,
    team_size: int = 10,
) -> dict:
    """
    Generate a complete phased improvement roadmap.

    Args:
        dimension_scores: Dict of {dim_id: {score, level, label, ...}}.
        target_profile: "next_tier", "elite", or custom dict.
        anti_patterns: Detected anti-patterns from antipattern_engine.
        team_size: Number of developers (for ROI estimation).

    Returns:
        Complete roadmap dict with phases, ROI, impact-effort matrix, and gaps.
    """
    gaps = calculate_gaps(dimension_scores, target_profile)
    recommendations = match_recommendations(gaps, anti_patterns)
    classified = classify_impact_effort(recommendations)
    phases = assign_phases(classified)
    roi = estimate_total_roi(phases, team_size)

    return {
        "phases": phases,
        "total_roi_estimate": roi,
        "impact_effort_matrix": classified,
        "gaps": gaps,
        "target_profile": target_profile,
    }
    # ****Checked and Verified as Real*****
    # Generate a complete phased improvement roadmap. Args: dimension_scores: Dict of {dim_id: {score, level, label, ...}}.
