"""Field normalization - Map external fields to canonical schema.
Implementation: Phase 5
"""


def normalize_to_canonical(df, source_system, event_type="deployment"):
    """Map external data fields to the canonical external_quality_metrics schema.

    Args:
        df: Raw DataFrame from external source
        source_system: Source identifier (jira, azure_devops, github, gitlab, csv_upload)
        event_type: Event type (deployment, incident, defect, pull_request, build, release)

    Returns:
        DataFrame with canonical columns
    """
    # TODO: Implement field mapping per source_system
    df = df.copy()
    df["source_system"] = source_system
    df["event_type"] = event_type
    return df
