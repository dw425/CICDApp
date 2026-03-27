"""Jenkins hygiene checks — 10 checks.
# ****Truth Agent Verified**** — 10 checks: jk_bi_01-03, jk_tq_01-02, jk_ic_01-02,
# jk_sc_01-03 (1 hard gate: jk_sc_02). Mock data included.
"""

import random
from ingestion.hygiene_extractors.base_extractor import BaseHygieneExtractor, HygieneCheck
from compass.scoring_constants import score_percentage, score_boolean, score_tiered, SPEED_TIERS


class JenkinsHygieneExtractor(BaseHygieneExtractor):
    platform = "jenkins"

    def run_checks(self) -> list[HygieneCheck]:
        d = self.raw_data or _mock_jenkins_data()
        return [
            HygieneCheck("jk_bi_01", "Build success rate", "jenkins", "build_integration", 3,
                         "builds", "SUCCESS / total × 100",
                         raw_value=d.get("build_success_pct", 75), score=score_percentage(d.get("build_success_pct", 75))),
            HygieneCheck("jk_bi_02", "Build speed (median)", "jenkins", "build_integration", 2,
                         "builds", "same tiers",
                         raw_value=d.get("build_speed_secs", 720), score=score_tiered(d.get("build_speed_secs", 720), SPEED_TIERS)),
            HygieneCheck("jk_bi_03", "SCM-triggered builds", "jenkins", "build_integration", 2,
                         "builds", "scm triggers / total × 100",
                         raw_value=d.get("scm_trigger_pct", 55), score=score_percentage(d.get("scm_trigger_pct", 55))),

            HygieneCheck("jk_tq_01", "Test results present", "jenkins", "testing_quality", 3,
                         "test_reports", "jobs with reports / total × 100",
                         raw_value=d.get("test_report_pct", 45), score=score_percentage(d.get("test_report_pct", 45))),
            HygieneCheck("jk_tq_02", "Test pass rate", "jenkins", "testing_quality", 2,
                         "test_reports", "pass / total × 100",
                         raw_value=d.get("test_pass_rate", 85), score=score_percentage(d.get("test_pass_rate", 85))),

            HygieneCheck("jk_ic_01", "Pipeline-as-code (Jenkinsfile)", "jenkins", "iac_configuration", 3,
                         "job_configs", "pipeline_as_code jobs / total × 100",
                         raw_value=d.get("pipeline_as_code_pct", 40), score=score_percentage(d.get("pipeline_as_code_pct", 40))),
            HygieneCheck("jk_ic_02", "Multibranch pipelines", "jenkins", "iac_configuration", 2,
                         "job_configs", "multibranch / total × 100",
                         raw_value=d.get("multibranch_pct", 25), score=score_percentage(d.get("multibranch_pct", 25))),

            HygieneCheck("jk_sc_01", "No plugin security warnings", "jenkins", "security_compliance", 3,
                         "plugins", "0=100, 1-3=60, 4+=20",
                         raw_value=d.get("plugin_warnings", 2), score=100 if d.get("plugin_warnings", 2) == 0 else (60 if d.get("plugin_warnings", 2) <= 3 else 20)),
            HygieneCheck("jk_sc_02", "Credentials in vault", "jenkins", "security_compliance", 3,
                         "credentials", "vault refs / total cred refs × 100", hard_gate=True,
                         raw_value=d.get("vault_cred_pct", 60), score=score_percentage(d.get("vault_cred_pct", 60))),
            HygieneCheck("jk_sc_03", "No outdated plugins", "jenkins", "security_compliance", 2,
                         "plugins", "up-to-date / total × 100",
                         raw_value=d.get("plugin_uptodate_pct", 70), score=score_percentage(d.get("plugin_uptodate_pct", 70))),
        ]


def _mock_jenkins_data() -> dict:
    return {
        "build_success_pct": random.randint(60, 85),
        "build_speed_secs": random.choice([480, 720, 1200]),
        "scm_trigger_pct": random.randint(30, 70),
        "test_report_pct": random.randint(25, 60),
        "test_pass_rate": random.randint(75, 95),
        "pipeline_as_code_pct": random.randint(20, 60),
        "multibranch_pct": random.randint(10, 40),
        "plugin_warnings": random.choice([0, 1, 2, 3]),
        "vault_cred_pct": random.randint(40, 80),
        "plugin_uptodate_pct": random.randint(50, 85),
    }
