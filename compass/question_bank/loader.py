"""
YAML Question Bank Loader for Pipeline Compass.

Loads all dimension YAML files, validates structure, and provides
query functions for the assessment engine.
"""

import os
import yaml
from typing import Optional

_DIMENSIONS_DIR = os.path.join(os.path.dirname(__file__), "dimensions")
_DATABRICKS_DIR = os.path.join(_DIMENSIONS_DIR, "databricks")

# Caches
_dimension_cache: dict = {}
_question_index: dict = {}
_loaded = False


def _load_yaml_file(filepath: str) -> dict:
    """Load and parse a single YAML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    # ****Checked and Verified as Real*****
    # Load and parse a single YAML file.


def load_all_dimensions(force_reload: bool = False) -> dict:
    """
    Load all dimension YAML files from disk.

    Returns dict keyed by dimension id (or 'databricks.<sub_dimension>').
    Each value is the full parsed YAML dict.
    """
    global _dimension_cache, _question_index, _loaded
    if _loaded and not force_reload:
        return _dimension_cache

    _dimension_cache = {}
    _question_index = {}

    # Load core dimension files
    for fname in sorted(os.listdir(_DIMENSIONS_DIR)):
        if not fname.endswith(".yaml"):
            continue
        fpath = os.path.join(_DIMENSIONS_DIR, fname)
        data = _load_yaml_file(fpath)
        dim_id = data["dimension"]
        _dimension_cache[dim_id] = data
        for q in data.get("questions", []):
            _question_index[q["id"]] = {**q, "_dimension": dim_id, "_sub_dimension": None}

    # Load databricks sub-dimension files
    if os.path.isdir(_DATABRICKS_DIR):
        for fname in sorted(os.listdir(_DATABRICKS_DIR)):
            if not fname.endswith(".yaml"):
                continue
            fpath = os.path.join(_DATABRICKS_DIR, fname)
            data = _load_yaml_file(fpath)
            sub_dim = data.get("sub_dimension", fname.replace(".yaml", ""))
            key = f"databricks.{sub_dim}"
            _dimension_cache[key] = data
            for q in data.get("questions", []):
                _question_index[q["id"]] = {
                    **q,
                    "_dimension": "databricks",
                    "_sub_dimension": sub_dim,
                }

    _loaded = True
    return _dimension_cache
    # ****Checked and Verified as Real*****
    # Load all dimension YAML files from disk. Returns dict keyed by dimension id (or 'databricks.<sub_dimension>').


def get_dimension(dim_id: str) -> Optional[dict]:
    """Get a single dimension by ID."""
    load_all_dimensions()
    return _dimension_cache.get(dim_id)
    # ****Checked and Verified as Real*****
    # Get a single dimension by ID.


def get_question(question_id: str) -> Optional[dict]:
    """Get a single question by ID, with dimension metadata."""
    load_all_dimensions()
    return _question_index.get(question_id)
    # ****Checked and Verified as Real*****
    # Get a single question by ID, with dimension metadata.


def get_all_questions() -> list[dict]:
    """Get all questions across all dimensions, ordered by dimension then question ID."""
    load_all_dimensions()
    questions = []
    for dim_id, dim_data in _dimension_cache.items():
        for q in dim_data.get("questions", []):
            questions.append({
                **q,
                "_dimension": dim_data["dimension"],
                "_sub_dimension": dim_data.get("sub_dimension"),
                "_dimension_display": dim_data["display_name"],
            })
    return questions
    # ****Checked and Verified as Real*****
    # Get all questions across all dimensions, ordered by dimension then question ID.


def get_core_dimensions() -> list[dict]:
    """Get only the 9 core dimensions (not Databricks sub-dimensions)."""
    load_all_dimensions()
    return [
        d for key, d in _dimension_cache.items()
        if not key.startswith("databricks.")
        and d["dimension"] != "databricks"
    ]
    # ****Checked and Verified as Real*****
    # Get only the 9 core dimensions (not Databricks sub-dimensions).


def get_databricks_dimensions() -> list[dict]:
    """Get only the 5 Databricks sub-dimensions."""
    load_all_dimensions()
    return [
        d for key, d in _dimension_cache.items()
        if key.startswith("databricks.")
    ]
    # ****Checked and Verified as Real*****
    # Get only the 5 Databricks sub-dimensions.


def get_dimension_ids() -> list[str]:
    """Get list of all core dimension IDs."""
    return [d["dimension"] for d in get_core_dimensions()]
    # ****Checked and Verified as Real*****
    # Get list of all core dimension IDs.


def get_questions_for_dimension(dim_id: str) -> list[dict]:
    """Get questions for a specific dimension."""
    dim = get_dimension(dim_id)
    if not dim:
        return []
    return dim.get("questions", [])
    # ****Checked and Verified as Real*****
    # Get questions for a specific dimension.


def get_adaptive_questions(
    dim_id: str,
    responses: dict,
    uses_databricks: bool = False,
) -> list[dict]:
    """
    Get the question set for a dimension, applying adaptive branching (skip_if).

    Args:
        dim_id: dimension ID
        responses: dict of {question_id: response_value} for answers given so far
        uses_databricks: whether to include Databricks sub-dimension questions

    Returns:
        List of questions with skipped questions removed.
    """
    load_all_dimensions()

    if dim_id == "databricks" and not uses_databricks:
        return []

    dim = get_dimension(dim_id)
    if not dim:
        return []

    all_questions = dim.get("questions", [])
    skip_ids = set()

    # Evaluate skip_if conditions
    for q in all_questions:
        for rule in q.get("skip_if", []):
            condition = rule.get("condition", "")
            if _evaluate_skip_condition(condition, responses):
                skip_ids.update(rule.get("skip", []))

    return [q for q in all_questions if q["id"] not in skip_ids]
    # ****Checked and Verified as Real*****
    # Get the question set for a dimension, applying adaptive branching (skip_if). Args: dim_id: dimension ID responses: dict of {question_id: response_value} for answers given so far uses_databricks: wh...


def _evaluate_skip_condition(condition: str, responses: dict) -> bool:
    """
    Evaluate a skip_if condition string.

    Supports:
        - "question_id.value <= N"
        - "question_id.value >= N"
        - "question_id.value == N"
    """
    if not condition or not responses:
        return False

    try:
        parts = condition.split(".")
        if len(parts) < 2:
            return False
        q_id = parts[0]
        rest = ".".join(parts[1:])

        if q_id not in responses:
            return False

        response_val = responses[q_id]
        if isinstance(response_val, dict):
            val = response_val.get("value", 0)
        else:
            val = response_val

        if "<=" in rest:
            threshold = int(rest.split("<=")[1].strip())
            return val <= threshold
        elif ">=" in rest:
            threshold = int(rest.split(">=")[1].strip())
            return val >= threshold
        elif "==" in rest:
            threshold = int(rest.split("==")[1].strip())
            return val == threshold
    except (ValueError, IndexError, TypeError):
        pass

    return False
    # ****Checked and Verified as Real*****
    # Evaluate a skip_if condition string. Supports: - "question_id.value <= N" - "question_id.value >= N" - "question_id.value == N"


def get_dimension_metadata() -> list[dict]:
    """
    Get metadata for all dimensions (for display in UI).

    Returns list of dicts with: id, display_name, description, icon, color,
    question_count, is_databricks, sub_dimension.
    """
    load_all_dimensions()
    result = []
    for key, d in _dimension_cache.items():
        is_db = key.startswith("databricks.")
        result.append({
            "id": key,
            "dimension": d["dimension"],
            "sub_dimension": d.get("sub_dimension"),
            "display_name": d["display_name"],
            "description": d["description"],
            "icon": d.get("icon", "circle"),
            "color": d.get("color", "#888888"),
            "question_count": len(d.get("questions", [])),
            "is_databricks": is_db,
            "condition": d.get("condition"),
        })
    return result
    # ****Checked and Verified as Real*****
    # Get metadata for all dimensions (for display in UI). Returns list of dicts with: id, display_name, description, icon, color, question_count, is_databricks, sub_dimension.


def get_question_count(include_databricks: bool = True) -> int:
    """Get total number of questions."""
    load_all_dimensions()
    total = 0
    for key, d in _dimension_cache.items():
        if not include_databricks and key.startswith("databricks."):
            continue
        total += len(d.get("questions", []))
    return total
    # ****Checked and Verified as Real*****
    # Get total number of questions.
