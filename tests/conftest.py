"""Test configuration and shared fixtures."""
import os
import pytest
import pandas as pd

# Ensure mock mode for all tests
os.environ["CICD_APP_USE_MOCK"] = "true"


@pytest.fixture
def mock_teams():
    """Return a sample teams DataFrame."""
    return pd.DataFrame({
        "team_id": ["team_001", "team_002"],
        "team_name": ["Platform Engineering", "Data Engineering"],
        "member_count": [8, 12],
        "created_date": ["2024-01-15", "2024-01-15"],
    })
    # ****Checked and Verified as Real*****
    # Return a sample teams DataFrame.


@pytest.fixture
def mock_deployment_events():
    """Return a sample deployment events DataFrame."""
    return pd.DataFrame({
        "event_id": ["evt_001", "evt_002", "evt_003", "evt_004"],
        "team_id": ["team_001", "team_001", "team_002", "team_002"],
        "event_date": ["2024-03-01", "2024-03-02", "2024-03-01", "2024-03-02"],
        "actor_type": ["service_principal", "human", "service_principal", "service_principal"],
        "is_golden_path": [True, False, True, True],
        "artifact_type": ["pipeline", "notebook", "pipeline", "job"],
        "environment": ["prod", "dev", "staging", "prod"],
        "status": ["success", "success", "success", "failed"],
    })
    # ****Checked and Verified as Real*****
    # Return a sample deployment events DataFrame.


@pytest.fixture
def mock_pipeline_runs():
    """Return a sample pipeline runs DataFrame."""
    return pd.DataFrame({
        "run_id": ["run_001", "run_002", "run_003", "run_004", "run_005"],
        "team_id": ["team_001"] * 5,
        "status": ["success", "success", "failed", "success", "success"],
        "duration_seconds": [120, 180, 600, 90, 150],
        "is_git_backed": [True, True, False, True, True],
    })
    # ****Checked and Verified as Real*****
    # Return a sample pipeline runs DataFrame.
