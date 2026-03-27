"""
DDL statements for the CI/CD Maturity Intelligence custom tables.

All tables use Delta format and are created within the configured
catalog.schema (default: ``lho_analytics.cicd``).

Usage::

    from data_layer.queries.ddl import DDL_STATEMENTS
    for name, ddl in DDL_STATEMENTS.items():
        spark.sql(ddl)
"""

from config.settings import get_full_table_name

# ---------------------------------------------------------------------------
# Team Registry
# ---------------------------------------------------------------------------
TEAM_REGISTRY_DDL = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('team_registry')} (
    team_id          STRING    NOT NULL  COMMENT 'Unique team identifier',
    team_name        STRING    NOT NULL  COMMENT 'Human-readable team name',
    member_count     INT                 COMMENT 'Number of team members',
    created_date     DATE                COMMENT 'Date the team was onboarded'
)
USING DELTA
COMMENT 'Registry of engineering teams tracked by the CI/CD maturity app'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
"""

# ---------------------------------------------------------------------------
# Deployment Events
# ---------------------------------------------------------------------------
DEPLOYMENT_EVENTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('deployment_events')} (
    event_id         STRING    NOT NULL  COMMENT 'Unique event identifier',
    team_id          STRING    NOT NULL  COMMENT 'FK to team_registry.team_id',
    event_date       DATE      NOT NULL  COMMENT 'Date of the deployment event',
    actor_type       STRING              COMMENT 'service_principal or human',
    actor_email      STRING              COMMENT 'Email or SPN identifier of the actor',
    is_golden_path   BOOLEAN             COMMENT 'Whether the deployment followed golden path',
    artifact_type    STRING              COMMENT 'notebook, job, pipeline, dlt_pipeline, sql_query',
    environment      STRING              COMMENT 'dev, staging, or prod',
    source_system    STRING              COMMENT 'Origin system (e.g. databricks)',
    status           STRING              COMMENT 'success or failed'
)
USING DELTA
PARTITIONED BY (environment)
COMMENT 'Captures every deployment event for golden-path and promotion scoring'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
"""

# ---------------------------------------------------------------------------
# Maturity Scores
# ---------------------------------------------------------------------------
MATURITY_SCORES_DDL = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('maturity_scores')} (
    score_id         STRING    NOT NULL  COMMENT 'Unique score record identifier',
    team_id          STRING    NOT NULL  COMMENT 'FK to team_registry.team_id',
    score_date       DATE      NOT NULL  COMMENT 'Date the score was computed',
    domain           STRING    NOT NULL  COMMENT 'Scoring domain key',
    raw_score        DOUBLE              COMMENT 'Unweighted domain score (0-100)',
    weighted_score   DOUBLE              COMMENT 'Score multiplied by domain weight',
    composite_score  DOUBLE              COMMENT 'Overall weighted composite score',
    maturity_tier    STRING              COMMENT 'Tier label derived from composite score'
)
USING DELTA
PARTITIONED BY (score_date)
COMMENT 'Daily per-team, per-domain maturity scores'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
"""

# ---------------------------------------------------------------------------
# Maturity Trends
# ---------------------------------------------------------------------------
MATURITY_TRENDS_DDL = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('maturity_trends')} (
    trend_id         STRING    NOT NULL  COMMENT 'Unique trend record identifier',
    team_id          STRING    NOT NULL  COMMENT 'FK to team_registry.team_id',
    period_start     DATE      NOT NULL  COMMENT 'Start of the rollup period',
    period_end       DATE      NOT NULL  COMMENT 'End of the rollup period',
    period_type      STRING    NOT NULL  COMMENT 'weekly or monthly',
    avg_score        DOUBLE              COMMENT 'Average composite score in the period',
    min_score        DOUBLE              COMMENT 'Minimum composite score in the period',
    max_score        DOUBLE              COMMENT 'Maximum composite score in the period',
    delta            DOUBLE              COMMENT 'Change vs. prior period'
)
USING DELTA
PARTITIONED BY (period_type)
COMMENT 'Aggregated maturity trend rollups for sparkline and trend charts'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
"""

# ---------------------------------------------------------------------------
# Coaching Alerts
# ---------------------------------------------------------------------------
COACHING_ALERTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('coaching_alerts')} (
    alert_id         STRING    NOT NULL  COMMENT 'Unique alert identifier',
    team_id          STRING    NOT NULL  COMMENT 'FK to team_registry.team_id',
    created_date     DATE      NOT NULL  COMMENT 'Date the alert was generated',
    severity         STRING    NOT NULL  COMMENT 'critical, warning, or info',
    alert_type       STRING              COMMENT 'regression, threshold, anomaly, milestone, trend',
    domain           STRING              COMMENT 'Scoring domain that triggered the alert',
    message          STRING              COMMENT 'Human-readable alert message',
    recommendation   STRING              COMMENT 'Actionable recommendation text',
    is_acknowledged  BOOLEAN             COMMENT 'Whether a team lead has acknowledged the alert'
)
USING DELTA
COMMENT 'Proactive coaching alerts surfaced by the scoring engine'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
"""

# ---------------------------------------------------------------------------
# External Quality Metrics
# ---------------------------------------------------------------------------
EXTERNAL_QUALITY_METRICS_DDL = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('external_quality_metrics')} (
    metric_id        STRING    NOT NULL  COMMENT 'Unique metric record identifier',
    team_id          STRING    NOT NULL  COMMENT 'FK to team_registry.team_id',
    source_system    STRING    NOT NULL  COMMENT 'jira or azure_devops',
    event_type       STRING    NOT NULL  COMMENT 'deployment, incident, defect, pull_request',
    event_date       DATE                COMMENT 'Date of the external event',
    title            STRING              COMMENT 'Event title or summary',
    status           STRING              COMMENT 'Current status of the event',
    priority         STRING              COMMENT 'Priority level',
    metadata         STRING              COMMENT 'JSON blob with source-specific metadata'
)
USING DELTA
PARTITIONED BY (source_system)
COMMENT 'Quality signals ingested from external systems (Jira, Azure DevOps)'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
"""

# ---------------------------------------------------------------------------
# Convenience mapping
# ---------------------------------------------------------------------------
DDL_STATEMENTS: dict[str, str] = {
    "team_registry": TEAM_REGISTRY_DDL,
    "deployment_events": DEPLOYMENT_EVENTS_DDL,
    "maturity_scores": MATURITY_SCORES_DDL,
    "maturity_trends": MATURITY_TRENDS_DDL,
    "coaching_alerts": COACHING_ALERTS_DDL,
    "external_quality_metrics": EXTERNAL_QUALITY_METRICS_DDL,
}
