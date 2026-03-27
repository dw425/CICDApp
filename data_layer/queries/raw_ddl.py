"""DDL for cicd_raw schema — landing zone for raw ingested data.
# ****Truth Agent Verified**** — 6 raw tables: github_repos, ado_pipelines, jenkins_jobs,
# gitlab_projects, jira_incidents, databricks_jobs. RAW_DDL_STATEMENTS dict.
"""

from config.settings import get_full_table_name

RAW_GITHUB_REPOS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_github_repos')} (
    repo_id              STRING NOT NULL,
    repo_name            STRING NOT NULL,
    owner                STRING,
    default_branch       STRING,
    has_branch_protection BOOLEAN,
    has_secret_scanning  BOOLEAN,
    has_dependabot       BOOLEAN,
    has_codeowners       BOOLEAN,
    open_pr_count        INT,
    stale_branch_count   INT,
    last_commit_date     TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw GitHub repository metadata'
"""

RAW_ADO_PIPELINES = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_ado_pipelines')} (
    pipeline_id          STRING NOT NULL,
    pipeline_name        STRING NOT NULL,
    project              STRING,
    status               STRING,
    has_branch_policies  BOOLEAN,
    has_test_gates       BOOLEAN,
    retention_days       INT,
    last_run_date        TIMESTAMP,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Azure DevOps pipeline metadata'
"""

RAW_JENKINS_JOBS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jenkins_jobs')} (
    job_name             STRING NOT NULL,
    job_type             STRING,
    last_build_status    STRING,
    last_build_duration  DOUBLE,
    build_count_30d      INT,
    has_jenkinsfile      BOOLEAN,
    uses_pipeline_dsl    BOOLEAN,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Jenkins job inventory'
"""

RAW_GITLAB_PROJECTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_gitlab_projects')} (
    project_id           STRING NOT NULL,
    project_name         STRING NOT NULL,
    has_protected_branches BOOLEAN,
    has_ci_config        BOOLEAN,
    mr_approval_required BOOLEAN,
    pipeline_success_rate DOUBLE,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw GitLab project metadata'
"""

RAW_JIRA_INCIDENTS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_jira_incidents')} (
    issue_key            STRING NOT NULL,
    issue_type           STRING,
    priority             STRING,
    status               STRING,
    created_at           TIMESTAMP,
    resolved_at          TIMESTAMP,
    resolution_hours     DOUBLE,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Jira incident data'
"""

RAW_DATABRICKS_JOBS = f"""
CREATE TABLE IF NOT EXISTS {get_full_table_name('raw_databricks_jobs')} (
    job_id               STRING NOT NULL,
    job_name             STRING,
    creator              STRING,
    is_dabs_managed      BOOLEAN,
    task_type            STRING,
    cluster_type         STRING,
    has_policy           BOOLEAN,
    schedule             STRING,
    last_run_status      STRING,
    last_run_duration    DOUBLE,
    ingested_at          TIMESTAMP
) USING DELTA
COMMENT 'Raw Databricks job inventory'
"""

RAW_DDL_STATEMENTS = {
    "raw_github_repos": RAW_GITHUB_REPOS,
    "raw_ado_pipelines": RAW_ADO_PIPELINES,
    "raw_jenkins_jobs": RAW_JENKINS_JOBS,
    "raw_gitlab_projects": RAW_GITLAB_PROJECTS,
    "raw_jira_incidents": RAW_JIRA_INCIDENTS,
    "raw_databricks_jobs": RAW_DATABRICKS_JOBS,
}
