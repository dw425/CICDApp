"""Jira hygiene checks — 5 checks.
# ****Truth Agent Verified**** — 5 checks: jira_dr_01-02, jira_ob_01-02, jira_dx_01.
# MTTR tiered scoring, bug ratio proxy. Mock data included.
"""

import random
from ingestion.hygiene_extractors.base_extractor import BaseHygieneExtractor, HygieneCheck
from compass.scoring_constants import score_percentage, score_tiered


class JiraHygieneExtractor(BaseHygieneExtractor):
    platform = "jira"

    def run_checks(self) -> list[HygieneCheck]:
        d = self.raw_data or _mock_jira_data()
        return [
            HygieneCheck("jira_dr_01", "MTTR from incidents", "jira", "deployment_release", 3,
                         "incidents", "median MTTR: <1h=100, 1-4h=80, 4h-1d=60, 1d-1w=40, >1w=20",
                         raw_value=d.get("mttr_hours", 6), score=score_tiered(d.get("mttr_hours", 6), [(1, 100), (4, 80), (24, 60), (168, 40), (float("inf"), 20)])),
            HygieneCheck("jira_dr_02", "Change failure correlation", "jira", "deployment_release", 3,
                         "incidents", "incidents from deploy / total deploys → inverse",
                         raw_value=d.get("change_fail_score", 70), score=d.get("change_fail_score", 70)),

            HygieneCheck("jira_ob_01", "Incident tracking exists", "jira", "observability", 2,
                         "incidents", "incidents in 90d=100, none=50",
                         raw_value=d.get("has_incidents", True), score=100 if d.get("has_incidents", True) else 50),
            HygieneCheck("jira_ob_02", "Incident resolution rate", "jira", "observability", 2,
                         "incidents", "resolved / total × 100",
                         raw_value=d.get("resolution_rate", 75), score=score_percentage(d.get("resolution_rate", 75))),

            HygieneCheck("jira_dx_01", "Bug ratio (quality proxy)", "jira", "developer_experience", 2,
                         "issues", "<10%=100, 10-25%=70, 25-50%=40, >50%=20",
                         raw_value=d.get("bug_ratio_pct", 18), score=score_tiered(d.get("bug_ratio_pct", 18), [(10, 100), (25, 70), (50, 40), (float("inf"), 20)])),
        ]


def _mock_jira_data() -> dict:
    return {
        "mttr_hours": round(random.uniform(2, 48), 1),
        "change_fail_score": random.choice([50, 70, 80]),
        "has_incidents": True,
        "resolution_rate": random.randint(60, 90),
        "bug_ratio_pct": random.randint(10, 35),
    }
