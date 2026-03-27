"""
Anti-Pattern Detection Engine for Pipeline Compass.

Detects CI/CD anti-patterns based on indicator strings collected
from assessment responses. Each anti-pattern has severity, affected
dimensions, specific recommendations, and effort estimates.
"""

ANTI_PATTERNS = [
    # ── Pipeline Anti-Patterns ──
    {
        "id": "ap_snowflake_pipelines",
        "name": "Snowflake Pipelines",
        "category": "pipeline",
        "severity": "high",
        "detection": ["pipeline_copypaste"],
        "impact_dimensions": ["pipeline_governance"],
        "description": "Each team maintains unique, hand-crafted pipeline configurations with no shared standards. This leads to inconsistent quality gates, duplicated effort, and inability to roll out org-wide changes quickly.",
        "recommendation": "Adopt the Golden Pipeline pattern. Extract common stages (lint, test, scan, deploy) into shared templates. Migrate to managed inheritance where services inherit by reference, with Insert Blocks for team-specific logic.",
        "effort": "high",
        "effort_days": 30,
        "expected_improvement": 20,
        "roi_category": "speed",
    },
    {
        "id": "ap_long_lived_branches",
        "name": "Long-Lived Feature Branches",
        "category": "pipeline",
        "severity": "high",
        "detection": ["long_lived_branches"],
        "impact_dimensions": ["build_integration"],
        "description": "Feature branches living for days or weeks before merge create large, risky integrations, merge conflicts, and delayed feedback. This is the #1 inhibitor of continuous integration.",
        "recommendation": "Adopt trunk-based development. Break features into small increments merged daily. Use feature flags (LaunchDarkly, Unleash) to decouple deployment from release. Target branches living less than 24 hours.",
        "effort": "medium",
        "effort_days": 15,
        "expected_improvement": 20,
        "roi_category": "speed",
    },
    {
        "id": "ap_slow_builds",
        "name": "Slow Build Feedback",
        "category": "pipeline",
        "severity": "medium",
        "detection": ["slow_builds"],
        "impact_dimensions": ["build_integration", "developer_experience"],
        "description": "Builds taking over 15 minutes break developer flow state, encourage context-switching, and discourage frequent commits. Research shows productivity drops sharply when feedback exceeds 10 minutes.",
        "recommendation": "Implement build caching (Gradle, Bazel, Turbopack), parallel test execution, and incremental builds. Profile your build to find the slowest stages. Target sub-10-minute feedback loops.",
        "effort": "medium",
        "effort_days": 10,
        "expected_improvement": 15,
        "roi_category": "speed",
    },
    {
        "id": "ap_flaky_tolerance",
        "name": "Flaky Test Tolerance",
        "category": "pipeline",
        "severity": "high",
        "detection": ["flaky_tests_unmanaged"],
        "impact_dimensions": ["testing_quality"],
        "description": "Tolerating flaky tests erodes trust in CI. Developers learn to ignore failures, retry blindly, or skip tests entirely. Over time this creates a 'boy who cried wolf' effect where real failures go unnoticed.",
        "recommendation": "Implement automated flaky test detection (fail-then-pass on same commit). Quarantine flaky tests so they report but don't block. Track 'PRs Impacted' metric to prioritize fixes. Tools: Trunk.io, BuildPulse, Datadog CI Visibility.",
        "effort": "medium",
        "effort_days": 5,
        "expected_improvement": 10,
        "roi_category": "quality",
    },
    {
        "id": "ap_secret_sprawl",
        "name": "Secret Sprawl",
        "category": "security",
        "severity": "critical",
        "detection": ["hardcoded_secrets", "pat_auth"],
        "impact_dimensions": ["security_compliance"],
        "description": "Credentials hardcoded in source code, pipeline configs, or stored as long-lived personal access tokens create a critical security vulnerability. A single leaked token can compromise the entire pipeline.",
        "recommendation": "Implement pre-commit secrets detection (GitGuardian, gitleaks). Migrate all credentials to a secrets vault (HashiCorp Vault, AWS Secrets Manager). For Databricks: adopt OIDC workload identity federation to eliminate stored secrets entirely.",
        "effort": "low",
        "effort_days": 3,
        "expected_improvement": 25,
        "roi_category": "risk",
    },
    {
        "id": "ap_manual_deploys",
        "name": "Manual Deployment Steps",
        "category": "pipeline",
        "severity": "high",
        "detection": ["manual_deployment"],
        "impact_dimensions": ["deployment_release"],
        "description": "Manual deployment processes (SSH, console access, running scripts by hand) are error-prone, unrepeatable, and create key-person dependencies. They also prevent rapid rollback during incidents.",
        "recommendation": "Automate all deployment steps via CI/CD pipeline. Replace manual approvals with approval-as-code (CODEOWNERS, required reviewers). Implement automated rollback on health check failure. Eliminate SSH/console access for deployments.",
        "effort": "medium",
        "effort_days": 10,
        "expected_improvement": 25,
        "roi_category": "speed",
    },
    # ── Databricks Anti-Patterns ──
    {
        "id": "ap_notebook_monolith",
        "name": "Notebook Monolith",
        "category": "databricks",
        "severity": "critical",
        "detection": ["notebook_monolith"],
        "impact_dimensions": ["testing_quality", "developer_experience"],
        "description": "All logic lives in Databricks notebooks with no modularization, testing, or code review. This prevents unit testing, makes refactoring dangerous, and creates 'notebook spaghetti' that only the original author understands.",
        "recommendation": "Decompose notebooks: extract transformation logic into shared Python modules with unit tests. Use notebooks only for exploration. Run production via Workflows/Jobs with packaged code (wheels). Adopt IDE-first development with Databricks Connect.",
        "effort": "high",
        "effort_days": 30,
        "expected_improvement": 25,
        "roi_category": "quality",
    },
    {
        "id": "ap_production_notebook",
        "name": "Production Notebook Execution",
        "category": "databricks",
        "severity": "high",
        "detection": ["production_notebook_execution"],
        "impact_dimensions": ["deployment_release", "testing_quality"],
        "description": "Running notebooks directly in production (interactive or scheduled) bypasses all CI/CD quality gates, makes rollback impossible, and couples execution to workspace state rather than versioned artifacts.",
        "recommendation": "Transition production workloads to Databricks Jobs/Workflows referencing packaged code (Python wheels or JARs). Reserve notebooks for exploratory analysis only. Define jobs in DABs for version control and environment promotion.",
        "effort": "medium",
        "effort_days": 15,
        "expected_improvement": 20,
        "roi_category": "quality",
    },
    {
        "id": "ap_no_dabs",
        "name": "No DABs Adoption",
        "category": "databricks",
        "severity": "high",
        "detection": ["no_dabs", "manual_databricks"],
        "impact_dimensions": ["iac_configuration", "pipeline_governance"],
        "description": "Databricks resources (jobs, pipelines, clusters) are created and managed manually through the UI, making them impossible to version control, review, or promote across environments consistently.",
        "recommendation": "Adopt Databricks Asset Bundles (DABs) for all resource definitions. Start with primary ETL jobs, define multi-target YAML (dev/staging/prod), integrate with CI/CD pipeline. Use service principals for deployment authentication.",
        "effort": "medium",
        "effort_days": 10,
        "expected_improvement": 20,
        "roi_category": "speed",
    },
    {
        "id": "ap_hive_metastore",
        "name": "hive_metastore Dependency",
        "category": "databricks",
        "severity": "medium",
        "detection": ["hive_metastore_only"],
        "impact_dimensions": ["security_compliance"],
        "description": "Reliance on the legacy hive_metastore prevents fine-grained access control, cross-workspace data sharing, data lineage tracking, and compliance with data governance requirements.",
        "recommendation": "Migrate production tables to Unity Catalog. Implement per-environment catalogs (dev/staging/prod), service principal access, and governance-as-code for catalog/schema/grant management via Terraform or DABs.",
        "effort": "high",
        "effort_days": 30,
        "expected_improvement": 15,
        "roi_category": "risk",
    },
    {
        "id": "ap_interactive_cluster_prod",
        "name": "Interactive Clusters for Production",
        "category": "databricks",
        "severity": "medium",
        "detection": ["interactive_cluster_production"],
        "impact_dimensions": ["iac_configuration", "artifact_management"],
        "description": "Using all-purpose interactive clusters for production workloads wastes compute cost (clusters stay running), prevents resource isolation, and makes cost attribution impossible.",
        "recommendation": "Define job clusters in DABs for production workloads. Enforce via cluster policies. Tag clusters for cost attribution. Reserve all-purpose clusters for development only. Use instance pools for faster startup.",
        "effort": "low",
        "effort_days": 3,
        "expected_improvement": 10,
        "roi_category": "cost",
    },
    {
        "id": "ap_no_dlt_expectations",
        "name": "DLT Pipelines Without Quality Expectations",
        "category": "databricks",
        "severity": "medium",
        "detection": ["dlt_no_expectations"],
        "impact_dimensions": ["testing_quality"],
        "description": "DLT pipelines without quality expectations allow bad data to flow through the medallion architecture unchecked, causing silent data corruption that's expensive to detect and fix after the fact.",
        "recommendation": "Add @dlt.expect / @dlt.expect_or_drop / @dlt.expect_or_fail expectations at every medallion layer. Start with Bronze ingestion constraints (not null, valid types), then Silver business rules, then Gold aggregation validations.",
        "effort": "low",
        "effort_days": 5,
        "expected_improvement": 15,
        "roi_category": "quality",
    },
]

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_COLORS = {
    "critical": "#DC2626",
    "high": "#EA580C",
    "medium": "#CA8A04",
    "low": "#65A30D",
}
CATEGORY_LABELS = {
    "pipeline": "Pipeline",
    "security": "Security",
    "databricks": "Databricks",
    "culture": "Culture",
}


def detect_anti_patterns(indicators: set, include_databricks: bool = True) -> list[dict]:
    """
    Given indicator strings from assessment responses, return matching anti-patterns.

    Args:
        indicators: Set of indicator strings (e.g. {"slow_builds", "notebook_monolith"}).
        include_databricks: Whether to include Databricks-specific anti-patterns.

    Returns:
        List of matching anti-pattern dicts, sorted by severity (critical first).
    """
    detected = []

    for ap in ANTI_PATTERNS:
        if not include_databricks and ap["category"] == "databricks":
            continue
        if any(ind in indicators for ind in ap["detection"]):
            detected.append({
                **ap,
                "severity_color": SEVERITY_COLORS.get(ap["severity"], "#888"),
                "category_label": CATEGORY_LABELS.get(ap["category"], ap["category"]),
            })

    detected.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))
    return detected


def get_anti_pattern_summary(detected: list[dict]) -> dict:
    """
    Summarize detected anti-patterns.

    Returns:
        Dict with: total, by_severity, by_category, critical_count.
    """
    by_severity = {}
    by_category = {}
    for ap in detected:
        sev = ap["severity"]
        cat = ap["category"]
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total": len(detected),
        "by_severity": by_severity,
        "by_category": by_category,
        "critical_count": by_severity.get("critical", 0),
        "high_count": by_severity.get("high", 0),
    }
