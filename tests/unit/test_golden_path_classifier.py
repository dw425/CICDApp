"""Tests for Golden Path Classifier."""

import pytest
from ingestion.golden_path_classifier import GoldenPathClassifier


@pytest.fixture
def classifier():
    return GoldenPathClassifier(
        team_registry={"team_001": ["user1@company.com", "user2@company.com"]},
        known_ci_ips=["10.0.1.100", "10.0.1.101"],
    )


class TestClassifySingle:
    def test_standard_with_token(self, classifier):
        event = {
            "actor_email": "cicd-bot@company.com",
            "action_name": "createJob",
            "golden_path_tag": True,
        }
        result = classifier.classify(event)
        assert result["classification"] == "standard"
        assert result["confidence"] >= 0.7

    def test_standard_with_service_principal(self, classifier):
        event = {
            "actor_email": "deploy-service@company.com",
            "action_name": "updateJob",
            "source_type": "git_backed",
        }
        result = classifier.classify(event)
        assert result["classification"] == "standard"

    def test_non_standard_human_no_signals(self, classifier):
        event = {
            "actor_email": "random@company.com",
            "action_name": "createNotebook",
        }
        result = classifier.classify(event)
        assert result["classification"] == "non_standard"

    def test_unknown_minimal_event(self, classifier):
        event = {
            "actor_email": "random@company.com",
            "action_name": "createJob",
            "source_ip_address": "10.0.1.100",  # known CI IP gives 10 pts
        }
        result = classifier.classify(event)
        # 10 pts from CI IP + 5 from API = 15 < 40, so unknown
        assert result["classification"] in ("non_standard", "unknown")

    def test_standard_with_ci_ip_and_sp(self, classifier):
        event = {
            "actor_email": "automation-bot@company.com",
            "action_name": "updatePipeline",
            "source_ip_address": "10.0.1.100",
        }
        result = classifier.classify(event)
        # SP (30) + CI IP (10) + API (5) = 45 >= 40 → standard
        assert result["classification"] == "standard"


class TestClassifyBatch:
    def test_batch_returns_all_events(self, classifier):
        events = [
            {"actor_email": "cicd@company.com", "golden_path_tag": True, "action_name": "createJob"},
            {"actor_email": "human@company.com", "action_name": "import"},
            {"actor_email": "deploy-service@company.com", "source_type": "git_backed", "action_name": "updateJob"},
        ]
        results = classifier.classify_batch(events)
        assert len(results) == 3
        assert all("classification" in r for r in results)

    def test_empty_batch(self, classifier):
        results = classifier.classify_batch([])
        assert results == []


class TestAdoptionMetrics:
    def test_metrics_structure(self, classifier):
        classified = [
            {"classification": "standard", "team_id": "team_001", "artifact_type": "pipeline",
             "timestamp": "2024-03-01T10:00:00"},
            {"classification": "non_standard", "team_id": "team_001", "artifact_type": "notebook",
             "timestamp": "2024-03-02T10:00:00"},
            {"classification": "standard", "team_id": "team_001", "artifact_type": "pipeline",
             "timestamp": "2024-03-03T10:00:00"},
        ]
        metrics = classifier.compute_adoption_metrics(classified)
        assert "total_deployments" in metrics
        assert "adoption_pct" in metrics
        assert "standard_count" in metrics
        assert "non_standard_count" in metrics
        assert metrics["total_deployments"] == 3
        assert metrics["standard_count"] == 2
        assert metrics["non_standard_count"] == 1

    def test_empty_classified(self, classifier):
        metrics = classifier.compute_adoption_metrics([])
        assert metrics["total_deployments"] == 0
        assert metrics["adoption_pct"] == 0

    def test_by_artifact_type(self, classifier):
        classified = [
            {"classification": "standard", "artifact_type": "pipeline", "timestamp": "2024-03-01"},
            {"classification": "non_standard", "artifact_type": "pipeline", "timestamp": "2024-03-01"},
            {"classification": "standard", "artifact_type": "notebook", "timestamp": "2024-03-01"},
        ]
        metrics = classifier.compute_adoption_metrics(classified)
        assert "pipeline" in metrics["by_artifact_type"]
        assert metrics["by_artifact_type"]["pipeline"]["standard"] == 1
        assert metrics["by_artifact_type"]["pipeline"]["non_standard"] == 1
