"""Scoring constants: tier maps, speed tiers, DORA benchmarks, weight profiles.
# ****Truth Agent Verified**** — TIER_MAP (L1-L5), TIER_COLORS, SPEED_TIERS, LEAD_TIME_TIERS,
# DEPLOY_FREQUENCY_TIERS, DORA_BENCHMARKS (4 metrics x 4 tiers), DORA_TIER_COLORS,
# DIMENSION_IDS (9 dims), score_to_tier, classify_dora, score_percentage,
# score_inverse_percentage, score_tiered, score_boolean, score_count_tiers
"""

TIER_MAP = [
    (0, 20, 1, "Initial"),
    (21, 40, 2, "Managed"),
    (41, 60, 3, "Defined"),
    (61, 80, 4, "Optimized"),
    (81, 100, 5, "Elite"),
]

TIER_COLORS = {
    1: "#EF4444",
    2: "#F97316",
    3: "#EAB308",
    4: "#22C55E",
    5: "#3B82F6",
}

TIER_LABELS = {1: "Initial", 2: "Managed", 3: "Defined", 4: "Optimized", 5: "Elite"}

# Speed tiers (seconds → score)
SPEED_TIERS = [
    (120, 100),
    (300, 80),
    (900, 60),
    (1800, 40),
    (float("inf"), 20),
]

# Lead time tiers (hours → score)
LEAD_TIME_TIERS = [
    (4, 100),
    (24, 80),
    (72, 60),
    (168, 40),
    (float("inf"), 20),
]

# Deploy frequency tiers (deploys/week → score)
DEPLOY_FREQUENCY_TIERS = [
    (7, 100),
    (3, 80),
    (1, 60),
    (0.25, 40),
    (0, 20),
]

# DORA benchmark thresholds
DORA_BENCHMARKS = {
    "deployment_frequency": [
        (1.0, "Elite"),
        (0.143, "High"),
        (0.033, "Medium"),
        (0, "Low"),
    ],
    "lead_time": [
        (1, "Elite"),
        (24, "High"),
        (168, "Medium"),
        (720, "Low"),
    ],
    "change_failure_rate": [
        (5, "Elite"),
        (10, "High"),
        (15, "Medium"),
        (100, "Low"),
    ],
    "recovery_time": [
        (1, "Elite"),
        (24, "High"),
        (168, "Medium"),
        (720, "Low"),
    ],
}

DORA_TIER_COLORS = {
    "Elite": "#3B82F6",
    "High": "#22C55E",
    "Medium": "#EAB308",
    "Low": "#EF4444",
    "Unknown": "#6B7280",
}

# 9 COMPASS dimensions
DIMENSION_IDS = [
    "build_integration",
    "testing_quality",
    "deployment_release",
    "security_compliance",
    "observability",
    "iac_configuration",
    "artifact_management",
    "developer_experience",
    "pipeline_governance",
]


def score_to_tier(score: float) -> tuple:
    for low, high, level, label in TIER_MAP:
        if low <= score <= high:
            return level, label
    return 5, "Elite"


def classify_dora(metric: str, value) -> str:
    if value is None:
        return "Unknown"
    benchmarks = DORA_BENCHMARKS.get(metric, [])
    for threshold, tier in benchmarks:
        if metric in ("change_failure_rate", "recovery_time", "lead_time"):
            if value <= threshold:
                return tier
        else:
            if value >= threshold:
                return tier
    return "Low"


def score_percentage(raw_value: float) -> float:
    return max(0, min(100, raw_value))


def score_inverse_percentage(raw_value: float) -> float:
    return max(0, min(100, 100 - raw_value))


def score_tiered(raw_value: float, tiers: list) -> float:
    for threshold, score in tiers:
        if raw_value <= threshold:
            return score
    return tiers[-1][1] if tiers else 0


def score_boolean(raw_value: bool, true_score: float = 100, false_score: float = 0) -> float:
    return true_score if raw_value else false_score


def score_count_tiers(count: int, tiers: list) -> float:
    for min_count, score in sorted(tiers, key=lambda t: t[0], reverse=True):
        if count >= min_count:
            return score
    return 0
