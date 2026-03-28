"""Remediation Engine — Generates specific fix recommendations for failing hygiene checks.

Uses a rule-based approach with templated recommendations. When an LLM is configured,
enriches recommendations with context-specific guidance.
"""

REMEDIATION_TEMPLATES = {
    # GitHub checks
    "gh_branch_protection": {
        "title": "Enable Branch Protection",
        "steps": [
            "Go to repository Settings → Branches → Branch protection rules",
            "Click 'Add branch protection rule'",
            "Set branch name pattern to 'main' (or your default branch)",
            "Check 'Require a pull request before merging'",
            "Set 'Required number of approvals' to at least 2",
            "Check 'Require status checks to pass before merging'",
            "Check 'Require branches to be up to date before merging'",
            "Click 'Create' to save the rule",
        ],
        "impact": "Prevents direct pushes to main, enforces code review",
        "effort": "low",
        "time_estimate": "15 minutes",
    },
    "gh_secret_scanning": {
        "title": "Enable Secret Scanning",
        "steps": [
            "Go to repository Settings → Code security and analysis",
            "Enable 'Secret scanning'",
            "Enable 'Push protection' to block commits containing secrets",
            "Review any existing secret scanning alerts",
            "Rotate any exposed secrets immediately",
            "Add pre-commit hooks (e.g., gitleaks) for local detection",
        ],
        "impact": "Prevents credential leaks, reduces security incidents",
        "effort": "low",
        "time_estimate": "30 minutes",
    },
    "gh_ci_test_step": {
        "title": "Add Test Step to CI Pipeline",
        "steps": [
            "Edit your workflow YAML file in .github/workflows/",
            "Add a test step after the build step:",
            "  - name: Run Tests",
            "    run: pytest tests/ -v --tb=short  # (or npm test, go test, etc.)",
            "Ensure test dependencies are installed in a prior step",
            "Set the test step as a required status check in branch protection",
        ],
        "impact": "Catches regressions before merge, improves code quality",
        "effort": "medium",
        "time_estimate": "1-2 hours",
    },
    "gh_security_scan": {
        "title": "Add Security Scanning to CI",
        "steps": [
            "Add CodeQL analysis to your workflow:",
            "  - uses: github/codeql-action/init@v3",
            "    with: { languages: 'python' }  # adjust for your language",
            "  - uses: github/codeql-action/analyze@v3",
            "Or add a third-party scanner (Trivy, Snyk, Semgrep):",
            "  - uses: aquasecurity/trivy-action@master",
            "    with: { scan-type: 'fs', severity: 'CRITICAL,HIGH' }",
            "Enable Dependabot for dependency vulnerability scanning",
        ],
        "impact": "Detects vulnerabilities before they reach production",
        "effort": "medium",
        "time_estimate": "1-2 hours",
    },
    # Jenkins checks
    "jk_pipeline_as_code": {
        "title": "Migrate to Pipeline-as-Code (Jenkinsfile)",
        "steps": [
            "Create a Jenkinsfile in the repository root",
            "Define pipeline stages: build, test, security scan, deploy",
            "Convert the existing freestyle job to a Pipeline job",
            "Configure SCM polling or webhook trigger",
            "Use shared libraries for common pipeline patterns",
        ],
        "impact": "Version-controlled pipelines, reproducible builds, easier auditing",
        "effort": "high",
        "time_estimate": "4-8 hours",
    },
    "jk_plugin_hygiene": {
        "title": "Update Jenkins Plugins",
        "steps": [
            "Go to Manage Jenkins → Manage Plugins → Updates",
            "Review all available updates, especially those with security fixes",
            "Take a backup before updating",
            "Update plugins in batches, testing between batches",
            "Remove any unused plugins to reduce attack surface",
        ],
        "impact": "Reduces security vulnerabilities, improves stability",
        "effort": "medium",
        "time_estimate": "2-3 hours",
    },
    # Databricks checks
    "db_dabs_adoption": {
        "title": "Adopt Databricks Asset Bundles (DABs)",
        "steps": [
            "Install the Databricks CLI: pip install databricks-cli",
            "Initialize a bundle: databricks bundle init",
            "Define your jobs in databricks.yml with git_source",
            "Configure multi-target deployment (dev/staging/prod)",
            "Use service principals for CI/CD authentication",
            "Set up GitHub Actions/ADO pipeline to run 'databricks bundle deploy'",
        ],
        "impact": "Infrastructure-as-code for Databricks, reproducible deployments",
        "effort": "high",
        "time_estimate": "1-2 days",
    },
    "db_unity_catalog": {
        "title": "Migrate to Unity Catalog",
        "steps": [
            "Identify all tables in hive_metastore that need migration",
            "Create a dedicated catalog and schemas in Unity Catalog",
            "Use CREATE TABLE ... AS SELECT to migrate data",
            "Update all notebook/job references to use 3-level namespace",
            "Set up appropriate permissions using GRANT statements",
            "Decommission hive_metastore references after validation",
        ],
        "impact": "Centralized governance, fine-grained access control, data lineage",
        "effort": "high",
        "time_estimate": "1-2 weeks",
    },
    "db_job_clusters": {
        "title": "Switch from Interactive to Job Clusters",
        "steps": [
            "Identify production jobs running on interactive clusters",
            "Create job cluster definitions with appropriate sizing",
            "Update job configurations to use new_cluster instead of existing_cluster_id",
            "Apply cluster policies to enforce cost controls",
            "Enable autoscaling for variable workloads",
        ],
        "impact": "Lower cost, better isolation, automatic termination",
        "effort": "medium",
        "time_estimate": "2-4 hours per job",
    },
    # Generic fallback
    "generic_improvement": {
        "title": "Address Hygiene Check Failure",
        "steps": [
            "Review the specific check criteria and current score",
            "Identify the root cause of the failure",
            "Create a ticket in your project tracker",
            "Implement the fix and verify the score improves",
            "Add monitoring to prevent regression",
        ],
        "impact": "Improves overall maturity score",
        "effort": "varies",
        "time_estimate": "varies",
    },
}


def get_remediation(check_id: str, check_context: dict = None) -> dict:
    """
    Get remediation steps for a specific failing hygiene check.

    Args:
        check_id: The hygiene check identifier (e.g., "gh_branch_protection")
        check_context: Optional context about the specific failure

    Returns: {
        "title": str,
        "steps": list[str],
        "impact": str,
        "effort": str,
        "time_estimate": str,
    }
    """
    # Try exact match first
    if check_id in REMEDIATION_TEMPLATES:
        return REMEDIATION_TEMPLATES[check_id].copy()

    # Try prefix match (e.g., "gh_" for GitHub)
    prefix = check_id.split("_")[0] + "_" if "_" in check_id else ""
    for key, template in REMEDIATION_TEMPLATES.items():
        if key.startswith(prefix):
            return template.copy()

    return REMEDIATION_TEMPLATES["generic_improvement"].copy()


def get_top_remediations(check_results: list[dict], limit: int = 5) -> list[dict]:
    """
    Get the top N most impactful remediations from a set of check results.

    Prioritizes: hard gates first, then lowest scores, then highest weights.
    """
    failing = [c for c in check_results if c.get("score", 100) < 70]

    # Sort: hard gates first, then by score (ascending), then by weight (descending)
    failing.sort(key=lambda c: (
        0 if c.get("hard_gate") else 1,
        c.get("score", 100),
        -c.get("weight", 1),
    ))

    results = []
    for check in failing[:limit]:
        check_id = check.get("check_id", check.get("id", ""))
        remediation = get_remediation(check_id, check)
        remediation["check_id"] = check_id
        remediation["check_name"] = check.get("check_name", check.get("name", check_id))
        remediation["current_score"] = check.get("score", 0)
        remediation["dimension"] = check.get("dimension", "")
        results.append(remediation)

    return results
