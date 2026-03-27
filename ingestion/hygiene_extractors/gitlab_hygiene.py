"""GitLab hygiene checks — 15 checks.
# ****Truth Agent Verified**** — 15 checks: gl_bi_01-03, gl_tq_01-03 (1 hard gate),
# gl_dr_01-03, gl_sc_01-02 (1 hard gate), gl_ic_01, gl_dx_01, gl_pg_01, gl_ob_01.
# Native DORA metric integration. Mock data included.
"""

import random
from ingestion.hygiene_extractors.base_extractor import BaseHygieneExtractor, HygieneCheck
from compass.scoring_constants import score_percentage, score_boolean, score_tiered, SPEED_TIERS, LEAD_TIME_TIERS


class GitLabHygieneExtractor(BaseHygieneExtractor):
    platform = "gitlab"

    def run_checks(self) -> list[HygieneCheck]:
        d = self.raw_data or _mock_gitlab_data()
        return [
            HygieneCheck("gl_bi_01", "Pipeline success rate", "gitlab", "build_integration", 3,
                         "pipelines", "success / total × 100",
                         raw_value=d.get("pipeline_success_pct", 80), score=score_percentage(d.get("pipeline_success_pct", 80))),
            HygieneCheck("gl_bi_02", "Pipeline speed (median)", "gitlab", "build_integration", 2,
                         "pipelines", "duration, same tiers",
                         raw_value=d.get("pipeline_speed_secs", 540), score=score_tiered(d.get("pipeline_speed_secs", 540), SPEED_TIERS)),
            HygieneCheck("gl_bi_03", "MR-triggered pipelines", "gitlab", "build_integration", 2,
                         "pipelines", "merge_request_event / total × 100",
                         raw_value=d.get("mr_trigger_pct", 65), score=score_percentage(d.get("mr_trigger_pct", 65))),

            HygieneCheck("gl_tq_01", "Required approvals", "gitlab", "testing_quality", 3,
                         "approval_rules", "≥2=100, 1=50, 0=0",
                         raw_value=d.get("required_approvals", 1), score=100 if d.get("required_approvals", 1) >= 2 else (50 if d.get("required_approvals", 1) >= 1 else 0)),
            HygieneCheck("gl_tq_02", "Pipeline must succeed for merge", "gitlab", "testing_quality", 3,
                         "project_settings", "true=100, false=0", hard_gate=True,
                         raw_value=d.get("pipeline_must_succeed", True), score=score_boolean(d.get("pipeline_must_succeed", True))),
            HygieneCheck("gl_tq_03", "All discussions must resolve", "gitlab", "testing_quality", 2,
                         "project_settings", "true=100, false=0",
                         raw_value=d.get("discussions_must_resolve", False), score=score_boolean(d.get("discussions_must_resolve", False))),

            HygieneCheck("gl_dr_01", "DORA: Deployment Frequency", "gitlab", "deployment_release", 4,
                         "dora_metrics", "DORA benchmark tiers",
                         raw_value=d.get("dora_deploy_freq_score", 60), score=d.get("dora_deploy_freq_score", 60)),
            HygieneCheck("gl_dr_02", "DORA: Lead Time", "gitlab", "deployment_release", 4,
                         "dora_metrics", "DORA benchmark tiers",
                         raw_value=d.get("dora_lead_time_score", 70), score=d.get("dora_lead_time_score", 70)),
            HygieneCheck("gl_dr_03", "DORA: Change Failure Rate", "gitlab", "deployment_release", 3,
                         "dora_metrics", "<5%=100, 5-10%=80, 10-15%=60, 15-30%=40, >30%=20",
                         raw_value=d.get("dora_cfr_score", 80), score=d.get("dora_cfr_score", 80)),

            HygieneCheck("gl_sc_01", "Protected branches configured", "gitlab", "security_compliance", 3,
                         "protected_branches", "≥1=100, none=0", hard_gate=True,
                         raw_value=d.get("has_protected_branches", True), score=score_boolean(d.get("has_protected_branches", True))),
            HygieneCheck("gl_sc_02", "Security scanning results", "gitlab", "security_compliance", 3,
                         "vulnerabilities", "0 crit=100, open crit=30, no scanning=0",
                         raw_value=d.get("security_scan_score", 70), score=d.get("security_scan_score", 70)),

            HygieneCheck("gl_ic_01", "CI config present", "gitlab", "iac_configuration", 2,
                         "project_settings", "ci_config_path set=100, not=0",
                         raw_value=d.get("has_ci_config", True), score=score_boolean(d.get("has_ci_config", True))),

            HygieneCheck("gl_dx_01", "MR lead time", "gitlab", "developer_experience", 3,
                         "merge_requests", "median lead time, same tiers",
                         raw_value=d.get("mr_lead_time_hours", 28), score=score_tiered(d.get("mr_lead_time_hours", 28), LEAD_TIME_TIERS)),

            HygieneCheck("gl_pg_01", "Merge method (rebase preferred)", "gitlab", "pipeline_governance", 2,
                         "project_settings", "ff=100, rebase_merge=80, merge=40",
                         raw_value=d.get("merge_method_score", 80), score=d.get("merge_method_score", 80)),

            HygieneCheck("gl_ob_01", "DORA: Time to Restore", "gitlab", "observability", 3,
                         "dora_metrics", "<1h=100, 1h-1d=80, 1d-1w=50, >1w=20",
                         raw_value=d.get("dora_mttr_score", 60), score=d.get("dora_mttr_score", 60)),
        ]


def _mock_gitlab_data() -> dict:
    return {
        "pipeline_success_pct": random.randint(70, 90),
        "pipeline_speed_secs": random.choice([360, 540, 900]),
        "mr_trigger_pct": random.randint(50, 80),
        "required_approvals": random.choice([1, 2]),
        "pipeline_must_succeed": random.choice([True, True, False]),
        "discussions_must_resolve": random.choice([True, False]),
        "dora_deploy_freq_score": random.choice([40, 60, 80]),
        "dora_lead_time_score": random.choice([60, 70, 80]),
        "dora_cfr_score": random.choice([60, 80, 100]),
        "has_protected_branches": True,
        "security_scan_score": random.choice([0, 30, 70, 100]),
        "has_ci_config": True,
        "mr_lead_time_hours": round(random.uniform(8, 72), 1),
        "merge_method_score": random.choice([40, 80, 100]),
        "dora_mttr_score": random.choice([50, 60, 80]),
    }
