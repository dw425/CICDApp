"""
CI/CD Data Source Slot Definitions.
# ****Truth Agent Verified**** — 6 CI/CD slots: deployment_events, pipeline_runs,
# pull_requests, work_items, incidents, repo_activity with canonical field schemas.

Each slot defines a canonical data shape the app needs. External sources
map their fields to one of these slots before data reaches the dashboard.
"""

DATA_SOURCE_SLOTS = {
    "deployment_events": {
        "label": "Deployment Events",
        "description": "Deployment lifecycle events for golden-path and environment promotion scoring.",
        "target_table": "deployment_events",
        "scoring_domains": ["golden_path", "environment_promotion"],
        "fields": [
            {"name": "event_id", "type": "STRING", "required": True, "description": "Unique event identifier"},
            {"name": "team_id", "type": "STRING", "required": True, "description": "Team identifier"},
            {"name": "event_date", "type": "DATE", "required": True, "description": "Date of deployment event"},
            {"name": "actor_type", "type": "STRING", "required": True, "description": "service_principal or human"},
            {"name": "actor_email", "type": "STRING", "required": False, "description": "Email or SPN identifier"},
            {"name": "is_golden_path", "type": "BOOLEAN", "required": True, "description": "Whether deployment followed golden path"},
            {"name": "artifact_type", "type": "STRING", "required": False, "description": "notebook, job, pipeline, dlt_pipeline, sql_query"},
            {"name": "environment", "type": "STRING", "required": True, "description": "dev, staging, or prod"},
            {"name": "source_system", "type": "STRING", "required": False, "description": "Origin system"},
            {"name": "status", "type": "STRING", "required": True, "description": "success or failed"},
        ],
    },
    "pipeline_runs": {
        "label": "Pipeline Runs",
        "description": "CI/CD pipeline execution records for reliability scoring.",
        "target_table": "pipeline_runs",
        "scoring_domains": ["pipeline_reliability"],
        "fields": [
            {"name": "run_id", "type": "STRING", "required": True, "description": "Unique run identifier"},
            {"name": "team_id", "type": "STRING", "required": True, "description": "Team identifier"},
            {"name": "run_date", "type": "DATE", "required": True, "description": "Date of pipeline run"},
            {"name": "pipeline_name", "type": "STRING", "required": False, "description": "Pipeline name"},
            {"name": "status", "type": "STRING", "required": True, "description": "success, failed, cancelled"},
            {"name": "duration_seconds", "type": "DOUBLE", "required": True, "description": "Run duration in seconds"},
            {"name": "trigger_type", "type": "STRING", "required": False, "description": "manual, scheduled, ci"},
            {"name": "source_system", "type": "STRING", "required": False, "description": "Origin system"},
        ],
    },
    "pull_requests": {
        "label": "Pull Requests",
        "description": "PR activity for golden-path and security governance scoring.",
        "target_table": "external_quality_metrics",
        "scoring_domains": ["golden_path", "security_governance"],
        "event_type": "pull_request",
        "fields": [
            {"name": "pr_id", "type": "STRING", "required": True, "description": "Unique PR identifier"},
            {"name": "team_id", "type": "STRING", "required": True, "description": "Team identifier"},
            {"name": "event_date", "type": "DATE", "required": True, "description": "PR created/merged date"},
            {"name": "title", "type": "STRING", "required": False, "description": "PR title"},
            {"name": "status", "type": "STRING", "required": True, "description": "open, merged, closed"},
            {"name": "source_system", "type": "STRING", "required": True, "description": "github, azure_devops, gitlab"},
            {"name": "repo_name", "type": "STRING", "required": False, "description": "Repository name"},
            {"name": "author", "type": "STRING", "required": False, "description": "PR author"},
            {"name": "reviewers_count", "type": "INT", "required": False, "description": "Number of reviewers"},
        ],
    },
    "work_items": {
        "label": "Work Items",
        "description": "Work items (tasks, stories, bugs) for data quality and pipeline reliability.",
        "target_table": "external_quality_metrics",
        "scoring_domains": ["data_quality", "pipeline_reliability"],
        "event_type": "work_item",
        "fields": [
            {"name": "item_id", "type": "STRING", "required": True, "description": "Unique item identifier"},
            {"name": "team_id", "type": "STRING", "required": True, "description": "Team identifier"},
            {"name": "event_date", "type": "DATE", "required": True, "description": "Item created date"},
            {"name": "item_type", "type": "STRING", "required": True, "description": "task, story, bug, epic"},
            {"name": "title", "type": "STRING", "required": False, "description": "Item title"},
            {"name": "status", "type": "STRING", "required": True, "description": "open, in_progress, closed"},
            {"name": "priority", "type": "STRING", "required": False, "description": "Priority level"},
            {"name": "source_system", "type": "STRING", "required": True, "description": "jira, azure_devops"},
        ],
    },
    "incidents": {
        "label": "Incidents",
        "description": "Incident records for pipeline reliability and security governance.",
        "target_table": "external_quality_metrics",
        "scoring_domains": ["pipeline_reliability", "security_governance"],
        "event_type": "incident",
        "fields": [
            {"name": "incident_id", "type": "STRING", "required": True, "description": "Unique incident identifier"},
            {"name": "team_id", "type": "STRING", "required": True, "description": "Team identifier"},
            {"name": "event_date", "type": "DATE", "required": True, "description": "Incident reported date"},
            {"name": "severity", "type": "STRING", "required": True, "description": "critical, high, medium, low"},
            {"name": "title", "type": "STRING", "required": False, "description": "Incident title"},
            {"name": "status", "type": "STRING", "required": True, "description": "open, investigating, resolved"},
            {"name": "source_system", "type": "STRING", "required": True, "description": "jira, pagerduty, servicenow"},
            {"name": "resolution_hours", "type": "DOUBLE", "required": False, "description": "Hours to resolution"},
        ],
    },
    "repo_activity": {
        "label": "Repository Activity",
        "description": "Repo-level activity for golden-path and security governance.",
        "target_table": "external_quality_metrics",
        "scoring_domains": ["golden_path", "security_governance"],
        "event_type": "repo_activity",
        "fields": [
            {"name": "activity_id", "type": "STRING", "required": True, "description": "Unique activity identifier"},
            {"name": "team_id", "type": "STRING", "required": True, "description": "Team identifier"},
            {"name": "event_date", "type": "DATE", "required": True, "description": "Activity date"},
            {"name": "repo_name", "type": "STRING", "required": True, "description": "Repository name"},
            {"name": "activity_type", "type": "STRING", "required": False, "description": "commit, branch_create, tag, release"},
            {"name": "source_system", "type": "STRING", "required": True, "description": "github, gitlab, azure_devops"},
            {"name": "author", "type": "STRING", "required": False, "description": "Activity author"},
        ],
    },
}


def get_slot(slot_id):
    """Return slot definition by ID."""
    return DATA_SOURCE_SLOTS.get(slot_id)


def get_slot_choices():
    """Return list of (slot_id, label) tuples for dropdowns."""
    return [(k, v["label"]) for k, v in DATA_SOURCE_SLOTS.items()]


def get_required_fields(slot_id):
    """Return list of required field names for a slot."""
    slot = DATA_SOURCE_SLOTS.get(slot_id, {})
    return [f["name"] for f in slot.get("fields", []) if f["required"]]


def get_all_fields(slot_id):
    """Return list of all field dicts for a slot."""
    slot = DATA_SOURCE_SLOTS.get(slot_id, {})
    return slot.get("fields", [])
