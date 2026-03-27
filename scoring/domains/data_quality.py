"""Data Quality Scoring (15%)
Constraint coverage + DLT expectation pass rates.
"""
import pandas as pd

def compute_score(table_constraints: pd.DataFrame = None, dlt_expectations: pd.DataFrame = None) -> dict:
    """Compute data quality score.

    Factors:
    - Constraint coverage: % of tables with at least one constraint (50%)
    - DLT expectation pass rate (50%)
    """
    details = {}
    scores = []

    # Constraint coverage
    if table_constraints is not None and not table_constraints.empty:
        if "table_name" in table_constraints.columns:
            tables_with_constraints = table_constraints["table_name"].nunique()
            # Assume a baseline of tables (use count as proxy)
            constraint_score = min(100, tables_with_constraints * 10)  # 10 tables = 100
            scores.append(constraint_score * 0.5)
            details["tables_with_constraints"] = int(tables_with_constraints)
            details["constraint_types"] = table_constraints["constraint_type"].value_counts().to_dict() if "constraint_type" in table_constraints.columns else {}

    # DLT expectation pass rate
    if dlt_expectations is not None and not dlt_expectations.empty:
        if "pass_count" in dlt_expectations.columns and "fail_count" in dlt_expectations.columns:
            total_pass = dlt_expectations["pass_count"].astype(int).sum()
            total_fail = dlt_expectations["fail_count"].astype(int).sum()
            total_checks = total_pass + total_fail
            pass_rate = (total_pass / total_checks * 100) if total_checks > 0 else 0
            scores.append(pass_rate * 0.5)
            details["total_expectations"] = int(len(dlt_expectations))
            details["pass_rate"] = round(pass_rate, 1)

    if not scores:
        return {"raw_score": None, "details": details}

    # Redistribute weights if only one factor available
    if len(scores) == 1:
        raw_score = round(scores[0] * 2, 1)  # Scale up since only one factor
    else:
        raw_score = round(sum(scores), 1)

    return {"raw_score": raw_score, "details": details}
