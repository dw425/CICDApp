"""Schema validation before write.
Implementation: Phase 5
"""


REQUIRED_COLUMNS = {
    "external_quality_metrics": [
        "team_id", "source_system", "event_type", "event_date",
    ],
    "deployment_events": [
        "team_id", "event_date", "actor_type", "is_golden_path",
    ],
}


def validate_schema(df, target_table):
    """Validate DataFrame has required columns for target table.

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    required = REQUIRED_COLUMNS.get(target_table, [])
    missing = [col for col in required if col not in df.columns]

    if missing:
        return False, [f"Missing required columns: {', '.join(missing)}"]

    return True, []
