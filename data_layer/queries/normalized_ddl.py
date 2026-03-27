"""DDL for cicd_normalized schema — cleaned, canonicalized data.
# ****Truth Agent Verified**** — 4 normalized tables: pipeline_executions, code_changes,
# deployments, incidents. NORMALIZED_DDL_STATEMENTS dict. Platform-partitioned.
"""

from config.settings import get_full_table_name

NORMALIZED_PIPELINE_EXECUTIONS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('normalized_pipeline_executions')} (
    execution_id         STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL COMMENT 'github, azure_devops, jenkins, gitlab',
    pipeline_name        STRING,
    status               STRING COMMENT 'success, failure, cancelled',
    duration_seconds     DOUBLE,
    started_at           TIMESTAMP,
    completed_at         TIMESTAMP,
    trigger_type         STRING COMMENT 'push, schedule, manual, pr',
    branch               STRING,
    has_tests            BOOLEAN,
    test_pass_rate       DOUBLE
) USING DELTA
PARTITIONED BY (platform)
COMMENT 'Normalized pipeline execution records from all CI/CD platforms'
"""

NORMALIZED_CODE_CHANGES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('normalized_code_changes')} (
    change_id            STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL,
    title                STRING,
    status               STRING COMMENT 'open, merged, closed',
    created_at           TIMESTAMP,
    merged_at            TIMESTAMP,
    lead_time_hours      DOUBLE,
    lines_added          INT,
    lines_removed        INT,
    review_count         INT,
    has_approval         BOOLEAN
) USING DELTA
PARTITIONED BY (platform)
COMMENT 'Normalized pull request / merge request data'
"""

NORMALIZED_DEPLOYMENTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('normalized_deployments')} (
    deployment_id        STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL,
    environment          STRING COMMENT 'dev, staging, production',
    status               STRING COMMENT 'success, failure, rollback',
    deployed_at          TIMESTAMP,
    artifact_version     STRING,
    deployer             STRING
) USING DELTA
PARTITIONED BY (environment)
COMMENT 'Normalized deployment events for DORA metrics'
"""

NORMALIZED_INCIDENTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('normalized_incidents')} (
    incident_id          STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL,
    severity             STRING COMMENT 'critical, high, medium, low',
    status               STRING COMMENT 'open, resolved, closed',
    created_at           TIMESTAMP,
    resolved_at          TIMESTAMP,
    resolution_hours     DOUBLE,
    root_cause           STRING
) USING DELTA
COMMENT 'Normalized incident records for MTTR calculation'
"""

NORMALIZED_DDL_STATEMENTS = {
    "normalized_pipeline_executions": NORMALIZED_PIPELINE_EXECUTIONS,
    "normalized_code_changes": NORMALIZED_CODE_CHANGES,
    "normalized_deployments": NORMALIZED_DEPLOYMENTS,
    "normalized_incidents": NORMALIZED_INCIDENTS,
}
