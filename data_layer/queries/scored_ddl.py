"""DDL for cicd_scored schema — computed scores and metrics.
# ****Truth Agent Verified**** — 5 scored tables: hygiene_checks, dimension_telemetry,
# hybrid_scores, dora_metrics, compass_composite. SCORED_DDL_STATEMENTS dict.
"""

from config.settings import get_full_table_name

SCORED_HYGIENE_CHECKS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('scored_hygiene_checks')} (
    check_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL,
    check_name           STRING,
    dimension            STRING,
    weight               INT,
    hard_gate            BOOLEAN,
    raw_value            STRING,
    score                DOUBLE,
    status               STRING COMMENT 'pass, warn, fail',
    scored_at            TIMESTAMP
) USING DELTA
PARTITIONED BY (platform)
COMMENT 'Individual hygiene check scores per team per platform'
"""

SCORED_DIMENSION_TELEMETRY = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('scored_dimension_telemetry')} (
    team_id              STRING NOT NULL,
    dimension            STRING NOT NULL,
    telemetry_score      DOUBLE,
    check_count          INT,
    passing_count        INT,
    warning_count        INT,
    failing_count        INT,
    hard_gate_triggered  BOOLEAN,
    scored_at            TIMESTAMP
) USING DELTA
COMMENT 'Aggregated dimension-level telemetry scores'
"""

SCORED_HYBRID_SCORES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('scored_hybrid_scores')} (
    team_id              STRING NOT NULL,
    dimension            STRING NOT NULL,
    hybrid_score         DOUBLE,
    telemetry_score      DOUBLE,
    assessment_score     DOUBLE,
    confidence           STRING COMMENT 'high, medium, low, none',
    discrepancy_delta    DOUBLE,
    scored_at            TIMESTAMP
) USING DELTA
COMMENT 'Hybrid 70/30 blend scores per dimension'
"""

SCORED_DORA_METRICS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('scored_dora_metrics')} (
    team_id              STRING NOT NULL,
    metric_name          STRING NOT NULL COMMENT 'deployment_frequency, lead_time, etc.',
    metric_value         DOUBLE,
    metric_unit          STRING,
    tier                 STRING COMMENT 'Elite, High, Medium, Low',
    period_days          INT,
    computed_at          TIMESTAMP
) USING DELTA
COMMENT 'DORA 2025 metrics computed from normalized data'
"""

SCORED_COMPASS_COMPOSITE = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('scored_compass_composite')} (
    team_id              STRING NOT NULL,
    overall_score        DOUBLE,
    overall_level        INT,
    overall_label        STRING,
    weight_profile       STRING,
    archetype_id         STRING,
    archetype_name       STRING,
    scored_at            TIMESTAMP
) USING DELTA
COMMENT 'Top-level COMPASS composite scores with archetype classification'
"""

SCORED_DDL_STATEMENTS = {
    "scored_hygiene_checks": SCORED_HYGIENE_CHECKS,
    "scored_dimension_telemetry": SCORED_DIMENSION_TELEMETRY,
    "scored_hybrid_scores": SCORED_HYBRID_SCORES,
    "scored_dora_metrics": SCORED_DORA_METRICS,
    "scored_compass_composite": SCORED_COMPASS_COMPOSITE,
}
