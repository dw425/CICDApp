"""DDL for cicd_normalized schema — cleaned, canonicalized data.
6 normalized tables: pipeline_executions, code_changes, deployments, incidents,
repo_hygiene, test_executions. Platform-partitioned.
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

NORMALIZED_REPO_HYGIENE = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('normalized_repo_hygiene')} (
    repo_id              STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL,
    has_branch_protection BOOLEAN,
    required_reviewers   INT,
    has_ci_config        BOOLEAN,
    has_secret_scanning  BOOLEAN,
    has_vulnerability_scanning BOOLEAN,
    ci_trigger_pct       DOUBLE,
    build_success_pct    DOUBLE,
    test_coverage_pct    DOUBLE,
    environment_count    INT,
    normalized_at        TIMESTAMP
) USING DELTA
PARTITIONED BY (platform)
COMMENT 'Normalized repository hygiene data across all platforms'
"""

NORMALIZED_TEST_EXECUTIONS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('normalized_test_executions')} (
    test_run_id          STRING NOT NULL,
    team_id              STRING NOT NULL,
    platform             STRING NOT NULL,
    pipeline_name        STRING,
    build_id             STRING,
    total_tests          INT,
    passed_tests         INT,
    failed_tests         INT,
    skipped_tests        INT,
    duration_seconds     DOUBLE,
    pass_rate            DOUBLE,
    executed_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (platform)
COMMENT 'Normalized test execution results from all CI/CD platforms'
"""

NORMALIZED_DDL_STATEMENTS = {
    "normalized_pipeline_executions": NORMALIZED_PIPELINE_EXECUTIONS,
    "normalized_code_changes": NORMALIZED_CODE_CHANGES,
    "normalized_deployments": NORMALIZED_DEPLOYMENTS,
    "normalized_incidents": NORMALIZED_INCIDENTS,
    "normalized_repo_hygiene": NORMALIZED_REPO_HYGIENE,
    "normalized_test_executions": NORMALIZED_TEST_EXECUTIONS,
}
