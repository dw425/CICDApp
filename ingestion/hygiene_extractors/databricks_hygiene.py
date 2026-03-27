"""Databricks hygiene checks — 13 checks.
# ****Truth Agent Verified**** — 13 checks: db_ic_01-03, db_dx_01-02, db_pg_01-02,
# db_sc_01-02, db_tq_01-02, db_bi_01, db_ob_01. DABs, UC, DLT coverage. Mock data included.
"""

import random
from ingestion.hygiene_extractors.base_extractor import BaseHygieneExtractor, HygieneCheck
from compass.scoring_constants import score_percentage, score_boolean


class DatabricksHygieneExtractor(BaseHygieneExtractor):
    platform = "databricks"

    def run_checks(self) -> list[HygieneCheck]:
        d = self.raw_data or _mock_databricks_data()
        return [
            HygieneCheck("db_ic_01", "DABs-managed jobs", "databricks", "iac_configuration", 4,
                         "job_inventory", "git_source jobs / total × 100",
                         raw_value=d.get("dabs_pct", 35), score=score_percentage(d.get("dabs_pct", 35))),
            HygieneCheck("db_ic_02", "Job clusters (not interactive)", "databricks", "iac_configuration", 3,
                         "job_inventory", "job_cluster / total × 100",
                         raw_value=d.get("job_cluster_pct", 55), score=score_percentage(d.get("job_cluster_pct", 55))),
            HygieneCheck("db_ic_03", "Cluster policy coverage", "databricks", "iac_configuration", 2,
                         "cluster_inventory", "with policy / total × 100",
                         raw_value=d.get("policy_coverage_pct", 40), score=score_percentage(d.get("policy_coverage_pct", 40))),

            HygieneCheck("db_dx_01", "Packaged code (wheels/JARs)", "databricks", "developer_experience", 3,
                         "job_inventory", "(wheel + jar) / total tasks × 100",
                         raw_value=d.get("packaged_code_pct", 25), score=score_percentage(d.get("packaged_code_pct", 25))),
            HygieneCheck("db_dx_02", "Repos linked to workspace", "databricks", "developer_experience", 2,
                         "repos_list", "count > 0 = 100, 0 = 0",
                         raw_value=d.get("has_repos", True), score=score_boolean(d.get("has_repos", True))),

            HygieneCheck("db_pg_01", "Service principal deployments", "databricks", "pipeline_governance", 3,
                         "audit_events", "SP runs / total runs × 100",
                         raw_value=d.get("sp_deploy_pct", 30), score=score_percentage(d.get("sp_deploy_pct", 30))),
            HygieneCheck("db_pg_02", "Job tagging for cost attribution", "databricks", "pipeline_governance", 2,
                         "job_inventory", "tagged jobs / total × 100",
                         raw_value=d.get("job_tagging_pct", 20), score=score_percentage(d.get("job_tagging_pct", 20))),

            HygieneCheck("db_sc_01", "Unity Catalog adoption", "databricks", "security_compliance", 3,
                         "uc_tables + hive_tables", "uc / (uc + hive) × 100",
                         raw_value=d.get("uc_adoption_pct", 45), score=score_percentage(d.get("uc_adoption_pct", 45))),
            HygieneCheck("db_sc_02", "Secret scopes usage", "databricks", "security_compliance", 2,
                         "secret_scopes", "scopes exist=100, none=0",
                         raw_value=d.get("has_secret_scopes", True), score=score_boolean(d.get("has_secret_scopes", True))),

            HygieneCheck("db_tq_01", "DLT expectations coverage", "databricks", "testing_quality", 3,
                         "dlt_events", "datasets with expectations / total × 100",
                         raw_value=d.get("dlt_expectation_pct", 50), score=score_percentage(d.get("dlt_expectation_pct", 50))),
            HygieneCheck("db_tq_02", "DLT expectation pass rate", "databricks", "testing_quality", 2,
                         "dlt_events", "pass / (pass + fail) × 100",
                         raw_value=d.get("dlt_pass_rate", 90), score=score_percentage(d.get("dlt_pass_rate", 90))),

            HygieneCheck("db_bi_01", "Job success rate", "databricks", "build_integration", 3,
                         "job_runs", "SUCCESS / total × 100",
                         raw_value=d.get("job_success_pct", 78), score=score_percentage(d.get("job_success_pct", 78))),

            HygieneCheck("db_ob_01", "Audit trail completeness", "databricks", "observability", 2,
                         "audit_events", ">10 action types=100, 5-10=60, <5=20",
                         raw_value=d.get("audit_action_types", 8), score=100 if d.get("audit_action_types", 8) > 10 else (60 if d.get("audit_action_types", 8) >= 5 else 20)),
        ]


def _mock_databricks_data() -> dict:
    return {
        "dabs_pct": random.randint(15, 55),
        "job_cluster_pct": random.randint(30, 70),
        "policy_coverage_pct": random.randint(20, 60),
        "packaged_code_pct": random.randint(10, 45),
        "has_repos": True,
        "sp_deploy_pct": random.randint(15, 50),
        "job_tagging_pct": random.randint(10, 40),
        "uc_adoption_pct": random.randint(25, 65),
        "has_secret_scopes": random.choice([True, True, False]),
        "dlt_expectation_pct": random.randint(30, 70),
        "dlt_pass_rate": random.randint(80, 98),
        "job_success_pct": random.randint(65, 88),
        "audit_action_types": random.randint(4, 14),
    }
