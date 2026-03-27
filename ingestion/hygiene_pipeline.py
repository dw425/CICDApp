"""
Hygiene Pipeline — Bridge between API connectors and hygiene extractors.

After a connector syncs, this module:
1. Calls the connector's fetch_repo_hygiene() method
2. Passes the result to the hygiene scorer
3. Returns scored results for display or storage
"""

from ingestion.api_connectors.registry import get_connector
from compass.hygiene_scorer import run_all_checks, aggregate_dimension_telemetry


def fetch_hygiene_from_connectors(data_sources: list[dict]) -> dict:
    """
    Fetch hygiene data from all configured data source connectors.

    Args:
        data_sources: List of data source config dicts, each with:
            - source_type: "github", "azure_devops", etc.
            - config: connector config dict

    Returns:
        Dict keyed by platform with raw hygiene data from each connector.
    """
    platform_data = {}

    for source in data_sources:
        source_type = source.get("source_type", "")
        config = source.get("config", {})

        try:
            connector = get_connector(source_type, config)
            if hasattr(connector, "fetch_repo_hygiene"):
                hygiene_data = connector.fetch_repo_hygiene()
                if hygiene_data:
                    platform_data[source_type] = hygiene_data
        except Exception:
            # Skip connectors that fail — others continue
            continue

    return platform_data


def run_hygiene_for_sources(data_sources: list[dict]) -> dict:
    """
    Full hygiene pipeline: fetch from connectors, run checks, aggregate.

    Args:
        data_sources: List of data source configs.

    Returns:
        Dict with: checks (list), telemetry (per-dimension), platform_data (raw).
    """
    platform_data = fetch_hygiene_from_connectors(data_sources)

    # Run hygiene checks using connector data (falls back to mock if no data)
    checks = run_all_checks(
        platform_data=platform_data,
        connected_platforms=list(platform_data.keys()) if platform_data else None,
    )

    # Aggregate per dimension
    telemetry = aggregate_dimension_telemetry(checks)

    return {
        "checks": checks,
        "telemetry": telemetry,
        "platform_data": platform_data,
    }


def run_hygiene_mock() -> dict:
    """Run hygiene pipeline with mock data (no connectors needed)."""
    checks = run_all_checks()  # Uses mock data from extractors
    telemetry = aggregate_dimension_telemetry(checks)
    return {
        "checks": checks,
        "telemetry": telemetry,
        "platform_data": {},
    }
