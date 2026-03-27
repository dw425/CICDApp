"""
Assessment Data Store for Pipeline Compass.

JSON-based persistence for organizations, assessments, and responses.
Supports CRUD operations with file-based storage in mock mode.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

_STORE_DIR = os.path.join(os.path.dirname(__file__), "data")
_ORGS_FILE = os.path.join(_STORE_DIR, "organizations.json")
_ASSESSMENTS_FILE = os.path.join(_STORE_DIR, "assessments.json")


def _ensure_store():
    """Ensure the data directory and files exist."""
    os.makedirs(_STORE_DIR, exist_ok=True)
    for fpath in [_ORGS_FILE, _ASSESSMENTS_FILE]:
        if not os.path.exists(fpath):
            with open(fpath, "w") as f:
                json.dump([], f)


def _read_json(filepath: str) -> list[dict]:
    """Read a JSON array from file."""
    _ensure_store()
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_json(filepath: str, data: list[dict]):
    """Write a JSON array to file."""
    _ensure_store()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Organization CRUD ──


def create_organization(
    name: str,
    industry: str = "",
    size: str = "",
    cloud_provider: str = "",
    uses_databricks: bool = False,
) -> dict:
    """Create a new organization."""
    org = {
        "id": str(uuid.uuid4()),
        "name": name,
        "industry": industry,
        "size": size,
        "cloud_provider": cloud_provider,
        "uses_databricks": uses_databricks,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    orgs = _read_json(_ORGS_FILE)
    orgs.append(org)
    _write_json(_ORGS_FILE, orgs)
    return org


def get_organization(org_id: str) -> Optional[dict]:
    """Get an organization by ID."""
    orgs = _read_json(_ORGS_FILE)
    for o in orgs:
        if o["id"] == org_id:
            return o
    return None


def get_all_organizations() -> list[dict]:
    """Get all organizations."""
    return _read_json(_ORGS_FILE)


def update_organization(org_id: str, updates: dict) -> Optional[dict]:
    """Update an organization's fields."""
    orgs = _read_json(_ORGS_FILE)
    for o in orgs:
        if o["id"] == org_id:
            o.update(updates)
            _write_json(_ORGS_FILE, orgs)
            return o
    return None


# ── Assessment CRUD ──


def create_assessment(
    org_id: str,
    assessment_type: str = "full",
    weight_profile: str = "balanced",
    respondent_name: str = "",
    respondent_role: str = "",
) -> dict:
    """Create a new assessment for an organization."""
    assessment = {
        "id": str(uuid.uuid4()),
        "org_id": org_id,
        "assessment_type": assessment_type,
        "status": "in_progress",
        "weight_profile": weight_profile,
        "respondent_name": respondent_name,
        "respondent_role": respondent_role,
        "responses": {},
        "scores": None,
        "composite": None,
        "anti_patterns": None,
        "roadmap": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    assessments = _read_json(_ASSESSMENTS_FILE)
    assessments.append(assessment)
    _write_json(_ASSESSMENTS_FILE, assessments)
    return assessment


def get_assessment(assessment_id: str) -> Optional[dict]:
    """Get an assessment by ID."""
    assessments = _read_json(_ASSESSMENTS_FILE)
    for a in assessments:
        if a["id"] == assessment_id:
            return a
    return None


def get_assessments_for_org(org_id: str) -> list[dict]:
    """Get all assessments for an organization."""
    assessments = _read_json(_ASSESSMENTS_FILE)
    return [a for a in assessments if a["org_id"] == org_id]


def get_all_assessments() -> list[dict]:
    """Get all assessments."""
    return _read_json(_ASSESSMENTS_FILE)


def update_assessment(assessment_id: str, updates: dict) -> Optional[dict]:
    """Update an assessment's fields."""
    assessments = _read_json(_ASSESSMENTS_FILE)
    for a in assessments:
        if a["id"] == assessment_id:
            a.update(updates)
            _write_json(_ASSESSMENTS_FILE, assessments)
            return a
    return None


def delete_assessment(assessment_id: str) -> bool:
    """Delete an assessment."""
    assessments = _read_json(_ASSESSMENTS_FILE)
    before = len(assessments)
    assessments = [a for a in assessments if a["id"] != assessment_id]
    if len(assessments) < before:
        _write_json(_ASSESSMENTS_FILE, assessments)
        return True
    return False


# ── Response Management ──


def save_response(
    assessment_id: str,
    question_id: str,
    dimension: str,
    sub_dimension: Optional[str],
    response_type: str,
    response_value: dict,
) -> Optional[dict]:
    """
    Save or update a single question response within an assessment.

    response_value format:
        likert/single_select: {"value": 3}
        binary: {"value": true}
        multi_select: {"values": ["a", "b"]}
        freeform: {"text": "..."}
    """
    assessments = _read_json(_ASSESSMENTS_FILE)
    for a in assessments:
        if a["id"] == assessment_id:
            if "responses" not in a or not isinstance(a["responses"], dict):
                a["responses"] = {}
            a["responses"][question_id] = {
                "question_id": question_id,
                "dimension": dimension,
                "sub_dimension": sub_dimension,
                "response_type": response_type,
                "response_value": response_value,
                "answered_at": datetime.now(timezone.utc).isoformat(),
            }
            _write_json(_ASSESSMENTS_FILE, assessments)
            return a["responses"][question_id]
    return None


def save_responses_batch(
    assessment_id: str,
    responses: list[dict],
) -> bool:
    """
    Save multiple responses at once.

    Each response dict must have: question_id, dimension, sub_dimension,
    response_type, response_value.
    """
    assessments = _read_json(_ASSESSMENTS_FILE)
    for a in assessments:
        if a["id"] == assessment_id:
            if "responses" not in a or not isinstance(a["responses"], dict):
                a["responses"] = {}
            for r in responses:
                a["responses"][r["question_id"]] = {
                    **r,
                    "answered_at": datetime.now(timezone.utc).isoformat(),
                }
            _write_json(_ASSESSMENTS_FILE, assessments)
            return True
    return False


def get_responses(assessment_id: str) -> dict:
    """Get all responses for an assessment as {question_id: response_dict}."""
    a = get_assessment(assessment_id)
    if a and isinstance(a.get("responses"), dict):
        return a["responses"]
    return {}


def get_response_count(assessment_id: str) -> int:
    """Get number of questions answered."""
    return len(get_responses(assessment_id))


# ── Score Storage ──


def save_scores(
    assessment_id: str,
    dimension_scores: dict,
    composite: dict,
    anti_patterns: list,
    roadmap: dict,
) -> bool:
    """Save computed scores, anti-patterns, and roadmap to an assessment."""
    return update_assessment(assessment_id, {
        "scores": dimension_scores,
        "composite": composite,
        "anti_patterns": anti_patterns,
        "roadmap": roadmap,
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }) is not None


# ── History ──


def get_completed_assessments(org_id: Optional[str] = None) -> list[dict]:
    """Get all completed assessments, optionally filtered by org."""
    assessments = _read_json(_ASSESSMENTS_FILE)
    result = [a for a in assessments if a.get("status") == "completed"]
    if org_id:
        result = [a for a in result if a.get("org_id") == org_id]
    result.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    return result
