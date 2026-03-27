"""DDL for cicd_raw schema — landing zone for raw ingested data.
Granular tables per platform per data type (33 total).
"""

from config.settings import get_full_table_name

# ── GitHub (7 tables) ──────────────────────────────────────────────────

RAW_GITHUB_WORKFLOW_RUNS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_workflow_runs')} (
    run_id               STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    workflow_name        STRING,
    status               STRING COMMENT 'completed, in_progress, queued',
    conclusion           STRING COMMENT 'success, failure, cancelled, skipped',
    duration_seconds     DOUBLE,
    started_at           TIMESTAMP,
    completed_at         TIMESTAMP,
    trigger_event        STRING COMMENT 'push, pull_request, schedule, workflow_dispatch',
    branch               STRING,
    commit_sha           STRING,
    is_pr_triggered      BOOLEAN,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitHub Actions workflow run records'
"""

RAW_GITHUB_PULL_REQUESTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_pull_requests')} (
    pr_id                STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    pr_number            INT,
    title                STRING,
    state                STRING COMMENT 'open, closed, merged',
    created_at           TIMESTAMP,
    merged_at            TIMESTAMP,
    closed_at            TIMESTAMP,
    lead_time_hours      DOUBLE,
    additions            INT,
    deletions            INT,
    changed_files        INT,
    review_comments      INT,
    is_draft             BOOLEAN,
    target_branch        STRING,
    source_branch        STRING,
    author               STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitHub pull request data with review metrics'
"""

RAW_GITHUB_COMMITS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_commits')} (
    commit_sha           STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    message              STRING,
    author               STRING,
    author_email         STRING,
    committed_at         TIMESTAMP,
    additions            INT,
    deletions            INT,
    files_changed        INT,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitHub commit records'
"""

RAW_GITHUB_REPO_HYGIENE = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_repo_hygiene')} (
    repo_id              STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    owner                STRING,
    default_branch       STRING,
    has_branch_protection BOOLEAN,
    required_reviewers   INT,
    has_status_checks    BOOLEAN,
    dismiss_stale_reviews BOOLEAN,
    has_secret_scanning  BOOLEAN,
    has_dependabot       BOOLEAN,
    has_code_scanning    BOOLEAN,
    has_codeowners       BOOLEAN,
    open_secret_alerts   INT,
    open_dependabot_alerts INT,
    critical_vulns       INT,
    environment_count    INT,
    ci_trigger_pct       DOUBLE,
    build_success_pct    DOUBLE,
    build_speed_secs     DOUBLE,
    test_workflow_pct    DOUBLE,
    security_workflow_pct DOUBLE,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitHub repository hygiene metadata'
"""

RAW_GITHUB_REPO_STATS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_repo_stats')} (
    repo_id              STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    commits_per_week     DOUBLE,
    contributors_count   INT,
    active_contributors_30d INT,
    open_issues_count    INT,
    forks_count          INT,
    watchers_count       INT,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw GitHub repository statistics'
"""

RAW_GITHUB_DEPLOYMENTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_deployments')} (
    deployment_id        STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    environment          STRING,
    status               STRING COMMENT 'success, failure, in_progress, inactive',
    created_at           TIMESTAMP,
    updated_at           TIMESTAMP,
    creator              STRING,
    ref                  STRING,
    sha                  STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitHub deployment records'
"""

RAW_GITHUB_SECURITY_ALERTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_security_alerts')} (
    alert_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    repo_name            STRING,
    alert_type           STRING COMMENT 'code_scanning, secret_scanning, dependabot',
    severity             STRING COMMENT 'critical, high, medium, low',
    state                STRING COMMENT 'open, fixed, dismissed',
    created_at           TIMESTAMP,
    fixed_at             TIMESTAMP,
    tool_name            STRING,
    rule_id              STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitHub security alerts (code scanning, secrets, dependabot)'
"""

# ── Azure DevOps (7 tables) ───────────────────────────────────────────

RAW_ADO_BUILDS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_builds')} (
    build_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    definition_name      STRING,
    status               STRING,
    result               STRING COMMENT 'succeeded, failed, canceled, partiallySucceeded',
    started_at           TIMESTAMP,
    completed_at         TIMESTAMP,
    duration_seconds     DOUBLE,
    source_branch        STRING,
    source_version       STRING,
    trigger_reason       STRING COMMENT 'manual, ci, schedule, pullRequest',
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Azure DevOps build records'
"""

RAW_ADO_PULL_REQUESTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_pull_requests')} (
    pr_id                STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    title                STRING,
    status               STRING COMMENT 'active, completed, abandoned',
    created_at           TIMESTAMP,
    closed_at            TIMESTAMP,
    merge_status         STRING,
    source_branch        STRING,
    target_branch        STRING,
    reviewer_count       INT,
    has_approval         BOOLEAN,
    author               STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Azure DevOps pull request records'
"""

RAW_ADO_TEST_RUNS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_test_runs')} (
    run_id               STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    build_id             STRING,
    name                 STRING,
    state                STRING COMMENT 'completed, inProgress, aborted',
    total_tests          INT,
    passed_tests         INT,
    failed_tests         INT,
    not_applicable_tests INT,
    started_at           TIMESTAMP,
    completed_at         TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Azure DevOps test run results'
"""

RAW_ADO_BRANCH_POLICIES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_branch_policies')} (
    policy_id            STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    policy_type          STRING COMMENT 'MinimumApproverCount, Build, RequiredReviewers, WorkItemLinking',
    is_enabled           BOOLEAN,
    is_blocking          BOOLEAN,
    branch_name          STRING,
    settings_json        STRING,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Azure DevOps branch policy configurations'
"""

RAW_ADO_RELEASES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_releases')} (
    release_id           STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    release_name         STRING,
    environment          STRING,
    status               STRING COMMENT 'succeeded, failed, canceled, partiallySucceeded',
    created_at           TIMESTAMP,
    deployed_at          TIMESTAMP,
    created_by           STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Azure DevOps release records'
"""

RAW_ADO_WORK_ITEMS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_work_items')} (
    work_item_id         STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    work_item_type       STRING COMMENT 'Bug, Task, UserStory, Feature',
    state                STRING,
    priority             INT,
    created_at           TIMESTAMP,
    resolved_at          TIMESTAMP,
    assigned_to          STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Azure DevOps work item records'
"""

RAW_ADO_BUILD_DEFINITIONS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_build_definitions')} (
    definition_id        STRING NOT NULL,
    team_id              STRING NOT NULL,
    project              STRING,
    name                 STRING,
    process_type         INT COMMENT '1=classic, 2=YAML',
    yaml_filename        STRING,
    repository_type      STRING,
    default_branch       STRING,
    created_at           TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Azure DevOps build/pipeline definitions'
"""

# ── Jenkins (5 tables) ────────────────────────────────────────────────

RAW_JENKINS_JOBS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jenkins_jobs')} (
    job_name             STRING NOT NULL,
    team_id              STRING NOT NULL,
    job_class            STRING COMMENT 'WorkflowJob, WorkflowMultiBranchProject, FreeStyleProject',
    job_url              STRING,
    color                STRING,
    last_build_number    INT,
    last_build_result    STRING,
    last_build_timestamp TIMESTAMP,
    last_build_duration  DOUBLE,
    is_pipeline_as_code  BOOLEAN,
    is_multibranch       BOOLEAN,
    has_scm_trigger      BOOLEAN,
    has_timer_trigger     BOOLEAN,
    has_test_publisher    BOOLEAN,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Jenkins job inventory with config analysis'
"""

RAW_JENKINS_BUILDS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jenkins_builds')} (
    build_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    job_name             STRING,
    build_number         INT,
    result               STRING COMMENT 'SUCCESS, FAILURE, UNSTABLE, ABORTED',
    duration_ms          BIGINT,
    started_at           TIMESTAMP,
    cause_description    STRING,
    cause_user           STRING,
    commit_count         INT,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Jenkins build history'
"""

RAW_JENKINS_JOB_CONFIGS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jenkins_job_configs')} (
    job_name             STRING NOT NULL,
    team_id              STRING NOT NULL,
    scm_type             STRING COMMENT 'git, svn, none',
    is_pipeline_as_code  BOOLEAN,
    is_multibranch       BOOLEAN,
    has_scm_trigger      BOOLEAN,
    has_timer_trigger     BOOLEAN,
    has_test_publisher    BOOLEAN,
    credential_ids       STRING COMMENT 'comma-separated credential IDs',
    config_hash          STRING,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Jenkins job configuration analysis from config.xml'
"""

RAW_JENKINS_TEST_REPORTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jenkins_test_reports')} (
    report_id            STRING NOT NULL,
    team_id              STRING NOT NULL,
    job_name             STRING,
    build_number         INT,
    total_count          INT,
    pass_count           INT,
    fail_count           INT,
    skip_count           INT,
    duration_seconds     DOUBLE,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Jenkins test report results'
"""

RAW_JENKINS_PLUGINS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jenkins_plugins')} (
    plugin_name          STRING NOT NULL,
    team_id              STRING NOT NULL,
    version              STRING,
    is_active            BOOLEAN,
    has_update           BOOLEAN,
    has_security_warning BOOLEAN,
    long_name            STRING,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Jenkins plugin inventory with update/security status'
"""

# ── GitLab (5 tables) ─────────────────────────────────────────────────

RAW_GITLAB_PIPELINES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_gitlab_pipelines')} (
    pipeline_id          STRING NOT NULL,
    team_id              STRING NOT NULL,
    project_id           STRING,
    status               STRING COMMENT 'success, failed, canceled, skipped, running',
    ref                  STRING,
    sha                  STRING,
    source               STRING COMMENT 'push, merge_request_event, schedule, api, web',
    duration_seconds     DOUBLE,
    created_at           TIMESTAMP,
    started_at           TIMESTAMP,
    finished_at          TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitLab CI/CD pipeline runs'
"""

RAW_GITLAB_MERGE_REQUESTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_gitlab_merge_requests')} (
    mr_id                STRING NOT NULL,
    team_id              STRING NOT NULL,
    project_id           STRING,
    title                STRING,
    state                STRING COMMENT 'opened, merged, closed',
    created_at           TIMESTAMP,
    merged_at            TIMESTAMP,
    closed_at            TIMESTAMP,
    lead_time_hours      DOUBLE,
    source_branch        STRING,
    target_branch        STRING,
    author               STRING,
    approvals_required   INT,
    approvals_received   INT,
    has_pipeline          BOOLEAN,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitLab merge request data with approval info'
"""

RAW_GITLAB_DORA_METRICS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_gitlab_dora_metrics')} (
    metric_id            STRING NOT NULL,
    team_id              STRING NOT NULL,
    project_id           STRING,
    metric_name          STRING COMMENT 'deployment_frequency, lead_time_for_changes, time_to_restore_service, change_failure_rate',
    metric_value         DOUBLE,
    date                 DATE,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitLab native DORA metric values'
"""

RAW_GITLAB_VULNERABILITIES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_gitlab_vulnerabilities')} (
    vulnerability_id     STRING NOT NULL,
    team_id              STRING NOT NULL,
    project_id           STRING,
    severity             STRING COMMENT 'critical, high, medium, low, info, unknown',
    state                STRING COMMENT 'detected, confirmed, resolved, dismissed',
    scanner              STRING,
    name                 STRING,
    detected_at          TIMESTAMP,
    resolved_at          TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw GitLab vulnerability findings'
"""

RAW_GITLAB_PROJECT_HYGIENE = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_gitlab_project_hygiene')} (
    project_id           STRING NOT NULL,
    team_id              STRING NOT NULL,
    project_name         STRING,
    has_ci_config        BOOLEAN,
    has_protected_branches BOOLEAN,
    mr_approval_required BOOLEAN,
    min_approvals        INT,
    has_push_rules       BOOLEAN,
    pipeline_success_rate DOUBLE,
    environment_count    INT,
    open_vulnerabilities INT,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw GitLab project-level hygiene metadata'
"""

# ── Jira (2 tables) ───────────────────────────────────────────────────

RAW_JIRA_ISSUES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jira_issues')} (
    issue_key            STRING NOT NULL,
    team_id              STRING NOT NULL,
    project_key          STRING,
    issue_type           STRING COMMENT 'Bug, Incident, Task, Story',
    priority             STRING COMMENT 'Blocker, Critical, Major, Minor, Trivial',
    status               STRING,
    summary              STRING,
    created_at           TIMESTAMP,
    updated_at           TIMESTAMP,
    resolved_at          TIMESTAMP,
    assignee             STRING,
    reporter             STRING,
    labels               STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Jira issue records'
"""

RAW_JIRA_ISSUE_CHANGELOGS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jira_issue_changelogs')} (
    changelog_id         STRING NOT NULL,
    team_id              STRING NOT NULL,
    issue_key            STRING,
    field                STRING COMMENT 'status, assignee, priority, etc.',
    from_value           STRING,
    to_value             STRING,
    changed_at           TIMESTAMP,
    author               STRING,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Jira issue changelog entries for MTTR calculation'
"""

# ── Databricks (7 tables) ─────────────────────────────────────────────

RAW_DATABRICKS_JOB_INVENTORY = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_job_inventory')} (
    job_id               STRING NOT NULL,
    team_id              STRING NOT NULL,
    job_name             STRING,
    creator              STRING,
    is_dabs_managed      BOOLEAN,
    has_git_source       BOOLEAN,
    task_count           INT,
    notebook_task_count  INT,
    python_wheel_count   INT,
    spark_jar_count      INT,
    cluster_type         STRING COMMENT 'new_cluster, existing_cluster_id, job_cluster',
    is_scheduled         BOOLEAN,
    schedule_cron        STRING,
    has_tags             BOOLEAN,
    tags_json            STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Databricks job inventory with task analysis'
"""

RAW_DATABRICKS_CLUSTER_INVENTORY = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_cluster_inventory')} (
    cluster_id           STRING NOT NULL,
    team_id              STRING NOT NULL,
    cluster_name         STRING,
    cluster_type         STRING COMMENT 'interactive, job, sql',
    state                STRING,
    autoscale_min        INT,
    autoscale_max        INT,
    node_type            STRING,
    spark_version        STRING,
    policy_id            STRING,
    has_policy           BOOLEAN,
    creator              STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Databricks cluster inventory'
"""

RAW_DATABRICKS_AUDIT_EVENTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_audit_events')} (
    event_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    event_type           STRING,
    action_name          STRING,
    user_identity        STRING,
    source_ip            STRING,
    request_params       STRING,
    event_time           TIMESTAMP,
    workspace_id         STRING,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Databricks audit log events from system.access.audit'
"""

RAW_DATABRICKS_UC_TABLES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_uc_tables')} (
    table_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    catalog_name         STRING,
    schema_name          STRING,
    table_name           STRING,
    table_type           STRING COMMENT 'MANAGED, EXTERNAL, VIEW',
    data_source_format   STRING,
    storage_location     STRING,
    owner                STRING,
    created_at           TIMESTAMP,
    updated_at           TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Unity Catalog table inventory'
"""

RAW_DATABRICKS_HIVE_TABLES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_hive_tables')} (
    database_name        STRING NOT NULL,
    table_name           STRING NOT NULL,
    team_id              STRING NOT NULL,
    table_type           STRING,
    data_source_format   STRING,
    storage_location     STRING,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw hive_metastore table inventory for UC adoption comparison'
"""

RAW_DATABRICKS_DLT_EVENTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_dlt_events')} (
    event_id             STRING NOT NULL,
    team_id              STRING NOT NULL,
    pipeline_id          STRING,
    pipeline_name        STRING,
    event_type           STRING COMMENT 'flow_progress, maintenance, planning',
    maturity_level       STRING,
    dataset_name         STRING,
    expectation_name     STRING,
    expectation_passed   BOOLEAN,
    records_total        BIGINT,
    records_failed       BIGINT,
    timestamp            TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw DLT pipeline events with data quality expectations'
"""

RAW_DATABRICKS_JOB_RUNS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_job_runs')} (
    run_id               STRING NOT NULL,
    team_id              STRING NOT NULL,
    job_id               STRING,
    job_name             STRING,
    state                STRING COMMENT 'RUNNING, TERMINATED, SKIPPED, INTERNAL_ERROR',
    result_state         STRING COMMENT 'SUCCESS, FAILED, TIMEDOUT, CANCELED',
    start_time           TIMESTAMP,
    end_time             TIMESTAMP,
    duration_seconds     DOUBLE,
    cluster_type         STRING,
    trigger_type         STRING COMMENT 'PERIODIC, ONE_TIME, RETRY, MANUAL',
    ingested_at          TIMESTAMP
) USING DELTA
PARTITIONED BY (team_id)
COMMENT 'Raw Databricks job run history'
"""

# ── Registry dict ─────────────────────────────────────────────────────

RAW_DDL_STATEMENTS = {
    # GitHub (7)
    "raw_github_workflow_runs": RAW_GITHUB_WORKFLOW_RUNS,
    "raw_github_pull_requests": RAW_GITHUB_PULL_REQUESTS,
    "raw_github_commits": RAW_GITHUB_COMMITS,
    "raw_github_repo_hygiene": RAW_GITHUB_REPO_HYGIENE,
    "raw_github_repo_stats": RAW_GITHUB_REPO_STATS,
    "raw_github_deployments": RAW_GITHUB_DEPLOYMENTS,
    "raw_github_security_alerts": RAW_GITHUB_SECURITY_ALERTS,
    # Azure DevOps (7)
    "raw_ado_builds": RAW_ADO_BUILDS,
    "raw_ado_pull_requests": RAW_ADO_PULL_REQUESTS,
    "raw_ado_test_runs": RAW_ADO_TEST_RUNS,
    "raw_ado_branch_policies": RAW_ADO_BRANCH_POLICIES,
    "raw_ado_releases": RAW_ADO_RELEASES,
    "raw_ado_work_items": RAW_ADO_WORK_ITEMS,
    "raw_ado_build_definitions": RAW_ADO_BUILD_DEFINITIONS,
    # Jenkins (5)
    "raw_jenkins_jobs": RAW_JENKINS_JOBS,
    "raw_jenkins_builds": RAW_JENKINS_BUILDS,
    "raw_jenkins_job_configs": RAW_JENKINS_JOB_CONFIGS,
    "raw_jenkins_test_reports": RAW_JENKINS_TEST_REPORTS,
    "raw_jenkins_plugins": RAW_JENKINS_PLUGINS,
    # GitLab (5)
    "raw_gitlab_pipelines": RAW_GITLAB_PIPELINES,
    "raw_gitlab_merge_requests": RAW_GITLAB_MERGE_REQUESTS,
    "raw_gitlab_dora_metrics": RAW_GITLAB_DORA_METRICS,
    "raw_gitlab_vulnerabilities": RAW_GITLAB_VULNERABILITIES,
    "raw_gitlab_project_hygiene": RAW_GITLAB_PROJECT_HYGIENE,
    # Jira (2)
    "raw_jira_issues": RAW_JIRA_ISSUES,
    "raw_jira_issue_changelogs": RAW_JIRA_ISSUE_CHANGELOGS,
    # Databricks (7)
    "raw_databricks_job_inventory": RAW_DATABRICKS_JOB_INVENTORY,
    "raw_databricks_cluster_inventory": RAW_DATABRICKS_CLUSTER_INVENTORY,
    "raw_databricks_audit_events": RAW_DATABRICKS_AUDIT_EVENTS,
    "raw_databricks_uc_tables": RAW_DATABRICKS_UC_TABLES,
    "raw_databricks_hive_tables": RAW_DATABRICKS_HIVE_TABLES,
    "raw_databricks_dlt_events": RAW_DATABRICKS_DLT_EVENTS,
    "raw_databricks_job_runs": RAW_DATABRICKS_JOB_RUNS,
}
