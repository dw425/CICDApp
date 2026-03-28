"""Tests for Sync Pipeline."""

import pytest
from ingestion.sync_pipeline import SyncPipeline, SyncResult, SyncReport


class TestSyncResult:
    def test_creation(self):
        result = SyncResult(
            platform="github",
            status="success",
            records_fetched=42,
        )
        assert result.platform == "github"
        assert result.status == "success"
        assert result.records_fetched == 42
        assert result.error_message == ""

    def test_error_result(self):
        result = SyncResult(
            platform="jenkins",
            status="error",
            error_message="Connection refused",
        )
        assert result.status == "error"
        assert "Connection" in result.error_message


class TestSyncReport:
    def test_add_result(self):
        report = SyncReport()
        report.add_result(SyncResult(platform="github", status="success", records_fetched=10, duration_ms=100))
        report.add_result(SyncResult(platform="jenkins", status="success", records_fetched=20, duration_ms=200))
        assert report.total_records == 30
        assert report.total_duration_ms == 300
        assert len(report.results) == 2


class TestSyncPipeline:
    def test_instantiation(self):
        pipeline = SyncPipeline()
        assert pipeline is not None

    def test_get_sync_history_empty(self):
        pipeline = SyncPipeline()
        history = pipeline.get_sync_history()
        assert isinstance(history, list)
        assert len(history) == 0
