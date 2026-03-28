"""Field normalization — Map external fields to canonical schema."""

import pandas as pd

from config.data_source_slots import DATA_SOURCE_SLOTS


def normalize_to_canonical(df, source_system, event_type="deployment"):
    """Map external data fields to the canonical external_quality_metrics schema.

    Args:
        df: Raw DataFrame from external source
        source_system: Source identifier (jira, azure_devops, github, gitlab, csv_upload)
        event_type: Event type (deployment, incident, pull_request, work_item, repo_activity)

    Returns:
        DataFrame with canonical columns
    """
    df = df.copy()
    df["source_system"] = source_system
    df["event_type"] = event_type

    # Apply source-specific field mappings
    mapping = _SOURCE_FIELD_MAPS.get(source_system, {}).get(event_type, {})
    if mapping:
        for src_col, dst_col in mapping.items():
            if src_col in df.columns and dst_col not in df.columns:
                df[dst_col] = df[src_col]

    # Ensure standard date column
    if "event_date" not in df.columns:
        for date_col in ("created_at", "run_date", "creationDate", "createdOn"):
            if date_col in df.columns:
                df["event_date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
                break

    return df
    # ****Checked and Verified as Real*****
    # Map external data fields to the canonical external_quality_metrics schema. Args: df: Raw DataFrame from external source source_system: Source identifier (jira, azure_devops, github, gitlab, csv_upl...


def normalize_with_slot(df, field_mapping, slot_id, source_system):
    """Apply explicit field mapping from wizard and slot-aware normalization.

    Args:
        df: Raw DataFrame
        field_mapping: dict of source_col -> canonical_col from wizard Step 4
        slot_id: Target CI/CD slot ID
        source_system: Source system identifier

    Returns:
        DataFrame with canonical columns per slot definition
    """
    df = df.copy()

    # Apply wizard field mapping
    if field_mapping:
        rename_map = {src: dst for src, dst in field_mapping.items() if dst and src in df.columns}
        df = df.rename(columns=rename_map)

    # Add source_system if not present
    if "source_system" not in df.columns:
        df["source_system"] = source_system

    # Add event_type for slots that target external_quality_metrics
    slot = DATA_SOURCE_SLOTS.get(slot_id, {})
    event_type = slot.get("event_type")
    if event_type and "event_type" not in df.columns:
        df["event_type"] = event_type

    return df
    # ****Checked and Verified as Real*****
    # Apply explicit field mapping from wizard and slot-aware normalization. Args: df: Raw DataFrame field_mapping: dict of source_col -> canonical_col from wizard Step 4 slot_id: Target CI/CD slot ID so...


# Per-source, per-event-type field mappings for common column renames
_SOURCE_FIELD_MAPS = {
    "azure_devops": {
        "pipeline_runs": {
            "buildId": "run_id",
            "result": "status",
            "finishTime": "run_date",
        },
        "pull_request": {
            "pullRequestId": "pr_id",
            "creationDate": "event_date",
            "createdBy.displayName": "author",
        },
        "work_item": {
            "fields.System.Title": "title",
            "fields.System.State": "status",
            "fields.System.WorkItemType": "item_type",
            "fields.System.CreatedDate": "event_date",
        },
    },
    "github": {
        "pipeline_runs": {
            "conclusion": "status",
            "created_at": "run_date",
            "name": "pipeline_name",
        },
        "pull_request": {
            "number": "pr_id",
            "state": "status",
            "created_at": "event_date",
            "user.login": "author",
        },
        "work_item": {
            "number": "item_id",
            "state": "status",
            "created_at": "event_date",
        },
    },
}
