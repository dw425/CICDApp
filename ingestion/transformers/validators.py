"""Schema validation before write."""

import pandas as pd

from config.data_source_slots import DATA_SOURCE_SLOTS


# Required columns per target table (base requirements)
REQUIRED_COLUMNS = {
    "external_quality_metrics": [
        "team_id", "source_system", "event_type", "event_date",
    ],
    "deployment_events": [
        "team_id", "event_date", "actor_type", "is_golden_path",
    ],
    "pipeline_runs": [
        "team_id", "run_date", "status", "duration_seconds",
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


def validate_for_slot(df, slot_id):
    """Validate DataFrame against a CI/CD slot's field requirements.

    Returns:
        list of dicts: [{"field": str, "passed": bool, "message": str}]
    """
    slot = DATA_SOURCE_SLOTS.get(slot_id)
    if slot is None:
        return [{"field": "", "passed": False, "message": f"Unknown slot: {slot_id}"}]

    results = []

    for field_def in slot.get("fields", []):
        name = field_def["name"]
        required = field_def["required"]
        field_type = field_def["type"]

        if name not in df.columns:
            if required:
                results.append({"field": name, "passed": False, "message": f"Required field '{name}' is missing"})
            continue

        # Check for nulls in required fields
        if required:
            null_count = df[name].isna().sum()
            if null_count > 0:
                results.append({
                    "field": name,
                    "passed": False,
                    "message": f"Required field '{name}' has {null_count} null values",
                })
            else:
                results.append({"field": name, "passed": True, "message": f"Field '{name}' present with no nulls"})

        # Type-specific checks
        if field_type == "DATE":
            try:
                pd.to_datetime(df[name].dropna().head(10))
                results.append({"field": name, "passed": True, "message": f"Field '{name}' dates are parseable"})
            except Exception:
                results.append({"field": name, "passed": False, "message": f"Field '{name}' contains unparseable dates"})

        elif field_type == "BOOLEAN":
            unique = set(df[name].dropna().unique())
            bool_values = {True, False, "true", "false", "True", "False", 1, 0, "1", "0"}
            if not unique.issubset(bool_values):
                results.append({
                    "field": name,
                    "passed": False,
                    "message": f"Field '{name}' has non-boolean values: {unique - bool_values}",
                })

    return results
