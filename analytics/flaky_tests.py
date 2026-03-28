"""Flaky Test Detection — Identifies tests that pass and fail on the same commit."""

from collections import defaultdict


def detect_flaky_tests(test_results: list[dict], flake_threshold: float = 0.1) -> list[dict]:
    """
    Identify flaky tests from test execution history.

    Args:
        test_results: List of dicts with keys:
            test_name, commit_sha, result (pass/fail), duration_seconds, executed_at
        flake_threshold: Minimum flake rate to flag (0-1)

    Returns:
        List of flaky tests: [{test_name, flake_rate, total_runs, pass_count, fail_count,
                                avg_duration, cluster_id, likely_cause}]
    """
    if not test_results:
        return []

    # Group results by test name
    by_test = defaultdict(list)
    for r in test_results:
        by_test[r.get("test_name", "unknown")].append(r)

    # Find tests with same-commit variance
    flaky = []
    for test_name, results in by_test.items():
        if len(results) < 5:
            continue

        total = len(results)
        passes = sum(1 for r in results if r.get("result") == "pass")
        fails = total - passes

        if passes == 0 or fails == 0:
            continue  # Consistently passing or failing = not flaky

        flake_rate = min(passes, fails) / total

        if flake_rate < flake_threshold:
            continue

        # Check for same-commit variance (the hallmark of flakiness)
        by_commit = defaultdict(set)
        for r in results:
            sha = r.get("commit_sha", "unknown")
            by_commit[sha].add(r.get("result", "unknown"))

        same_commit_variance = sum(1 for outcomes in by_commit.values() if len(outcomes) > 1)

        if same_commit_variance == 0 and flake_rate < 0.3:
            continue  # Different results on different commits might not be flaky

        # Analyze likely cause
        durations = [r.get("duration_seconds", 0) for r in results]
        avg_duration = sum(durations) / len(durations) if durations else 0
        duration_variance = _variance(durations)

        likely_cause = _infer_cause(test_name, results, duration_variance, avg_duration)

        flaky.append({
            "test_name": test_name,
            "flake_rate": round(flake_rate, 3),
            "total_runs": total,
            "pass_count": passes,
            "fail_count": fails,
            "same_commit_variance": same_commit_variance,
            "avg_duration": round(avg_duration, 2),
            "duration_variance": round(duration_variance, 2),
            "likely_cause": likely_cause,
        })

    flaky.sort(key=lambda x: x["flake_rate"], reverse=True)
    return flaky


def cluster_flaky_tests(flaky_tests: list[dict]) -> dict[str, list[str]]:
    """
    Cluster flaky tests by likely root cause.

    Returns: {cause: [test_name1, test_name2, ...]}
    """
    clusters = defaultdict(list)
    for test in flaky_tests:
        cause = test.get("likely_cause", "unknown")
        clusters[cause].append(test["test_name"])
    return dict(clusters)


def _variance(values: list[float]) -> float:
    """Compute variance of a list of numbers."""
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


def _infer_cause(test_name: str, results: list[dict], duration_var: float, avg_dur: float) -> str:
    """Infer likely cause of flakiness from patterns."""
    name_lower = test_name.lower()

    # Timing-related
    if duration_var > avg_dur * 2 and avg_dur > 5:
        return "timeout_sensitivity"

    # Database/state-related
    if any(kw in name_lower for kw in ("db", "database", "sql", "postgres", "mysql", "redis", "mongo")):
        return "database_state"

    # Network-related
    if any(kw in name_lower for kw in ("api", "http", "request", "fetch", "network", "connect")):
        return "network_dependency"

    # Concurrency-related
    if any(kw in name_lower for kw in ("concurrent", "parallel", "thread", "async", "race")):
        return "concurrency"

    # File system
    if any(kw in name_lower for kw in ("file", "path", "directory", "write", "read", "io")):
        return "filesystem_state"

    # Time-dependent
    if any(kw in name_lower for kw in ("time", "date", "clock", "schedule", "cron")):
        return "time_dependency"

    return "unknown"
