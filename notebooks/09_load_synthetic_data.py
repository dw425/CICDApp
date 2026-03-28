# Databricks notebook source
# MAGIC %md
# MAGIC # Load Synthetic Data
# MAGIC Populates the CI/CD Maturity lakehouse with realistic synthetic data
# MAGIC for 5 teams across all core tables.

# COMMAND ----------

import uuid
from datetime import datetime, timedelta, date
import random

catalog = spark.conf.get("spark.databricks.catalog", "lho_analytics")
schema = "cicd"

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

print(f"Loading synthetic data into {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Teams

# COMMAND ----------

teams = [
    ("team_001", "Platform Engineering", 12),
    ("team_002", "Data Engineering", 8),
    ("team_003", "ML Ops", 6),
    ("team_004", "Application Dev", 15),
    ("team_005", "Security & Compliance", 5),
]

team_rows = [(tid, tname, count, date(2024, 1, 15)) for tid, tname, count in teams]
df_teams = spark.createDataFrame(team_rows, ["team_id", "team_name", "member_count", "created_date"])
df_teams.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.team_registry")
print(f"  Loaded {df_teams.count()} teams")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deployment Events (90 days, ~2000 records)

# COMMAND ----------

random.seed(42)
envs = ["dev", "staging", "prod"]
artifact_types = ["notebook", "job", "pipeline", "dlt_pipeline", "sql_query"]
statuses = ["success", "success", "success", "success", "failed"]  # 80% success

deploy_rows = []
base_date = date(2026, 1, 1)

for team_id, _, _ in teams:
    # Each team gets different golden path ratios
    gp_ratio = {"team_001": 0.85, "team_002": 0.70, "team_003": 0.55, "team_004": 0.40, "team_005": 0.90}[team_id]
    daily_deploys = {"team_001": 8, "team_002": 5, "team_003": 3, "team_004": 6, "team_005": 2}[team_id]

    for day_offset in range(90):
        d = base_date + timedelta(days=day_offset)
        if d.weekday() >= 5:
            continue  # Skip weekends
        n = random.randint(max(1, daily_deploys - 2), daily_deploys + 3)
        for _ in range(n):
            is_gp = random.random() < gp_ratio
            actor = "service_principal" if is_gp else "human"
            deploy_rows.append((
                str(uuid.uuid4()), team_id, d,
                actor,
                f"{'spn-cicd@corp.com' if is_gp else 'dev-' + str(random.randint(1,20)) + '@corp.com'}",
                is_gp,
                random.choice(artifact_types),
                random.choice(envs),
                "databricks",
                random.choice(statuses),
            ))

df_deploy = spark.createDataFrame(deploy_rows, [
    "event_id", "team_id", "event_date", "actor_type", "actor_email",
    "is_golden_path", "artifact_type", "environment", "source_system", "status"
])
df_deploy.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.deployment_events")
print(f"  Loaded {df_deploy.count()} deployment events")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Maturity Scores (daily, 6 domains x 5 teams x 90 days)

# COMMAND ----------

from config.scoring_weights import DOMAIN_WEIGHTS  # noqa: E402

domains = ["golden_path", "environment_promotion", "pipeline_reliability", "data_quality", "security_governance", "cost_efficiency"]
weights = {"golden_path": 0.25, "environment_promotion": 0.15, "pipeline_reliability": 0.20, "data_quality": 0.15, "security_governance": 0.15, "cost_efficiency": 0.10}

# Team archetypes for score generation
team_profiles = {
    "team_001": {"golden_path": 82, "environment_promotion": 78, "pipeline_reliability": 88, "data_quality": 75, "security_governance": 85, "cost_efficiency": 70},
    "team_002": {"golden_path": 65, "environment_promotion": 72, "pipeline_reliability": 70, "data_quality": 85, "security_governance": 60, "cost_efficiency": 75},
    "team_003": {"golden_path": 50, "environment_promotion": 55, "pipeline_reliability": 60, "data_quality": 70, "security_governance": 45, "cost_efficiency": 55},
    "team_004": {"golden_path": 35, "environment_promotion": 40, "pipeline_reliability": 55, "data_quality": 45, "security_governance": 30, "cost_efficiency": 50},
    "team_005": {"golden_path": 88, "environment_promotion": 80, "pipeline_reliability": 75, "data_quality": 70, "security_governance": 92, "cost_efficiency": 65},
}

score_rows = []
for team_id in team_profiles:
    profile = team_profiles[team_id]
    for day_offset in range(90):
        d = base_date + timedelta(days=day_offset)
        # Slight upward trend + noise
        trend_bonus = day_offset * 0.05
        composite_parts = []
        for domain in domains:
            base_score = profile[domain] + trend_bonus + random.gauss(0, 3)
            raw = max(0, min(100, round(base_score, 2)))
            w = weights[domain]
            weighted = round(raw * w, 2)
            composite_parts.append(weighted)

            tier = "Initial" if raw < 21 else "Managed" if raw < 41 else "Defined" if raw < 61 else "Optimized" if raw < 81 else "Elite"
            score_rows.append((
                str(uuid.uuid4()), team_id, d, domain,
                raw, weighted, None, tier
            ))

        # Composite score row
        composite = round(sum(composite_parts), 2)
        c_tier = "Initial" if composite < 21 else "Managed" if composite < 41 else "Defined" if composite < 61 else "Optimized" if composite < 81 else "Elite"
        score_rows.append((
            str(uuid.uuid4()), team_id, d, "composite",
            composite, composite, composite, c_tier
        ))

df_scores = spark.createDataFrame(score_rows, [
    "score_id", "team_id", "score_date", "domain",
    "raw_score", "weighted_score", "composite_score", "maturity_tier"
])
df_scores.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.maturity_scores")
print(f"  Loaded {df_scores.count()} maturity score records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Maturity Trends (weekly rollups)

# COMMAND ----------

trend_rows = []
for team_id in team_profiles:
    profile = team_profiles[team_id]
    base_composite = sum(profile[d] * weights[d] for d in domains)
    for week in range(13):  # 13 weeks
        start = base_date + timedelta(weeks=week)
        end = start + timedelta(days=6)
        trend_bonus = week * 0.3
        avg = round(base_composite + trend_bonus + random.gauss(0, 1.5), 2)
        mn = round(avg - random.uniform(1, 4), 2)
        mx = round(avg + random.uniform(1, 4), 2)
        delta = round(random.gauss(0.3, 1.0), 2) if week > 0 else 0
        trend_rows.append((
            str(uuid.uuid4()), team_id, start, end, "weekly",
            avg, mn, mx, delta
        ))

df_trends = spark.createDataFrame(trend_rows, [
    "trend_id", "team_id", "period_start", "period_end", "period_type",
    "avg_score", "min_score", "max_score", "delta"
])
df_trends.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.maturity_trends")
print(f"  Loaded {df_trends.count()} trend records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Coaching Alerts

# COMMAND ----------

alert_templates = [
    ("critical", "regression", "golden_path", "Golden path adoption dropped below 50%", "Investigate recent manual deployments and enforce SPN-based CI/CD"),
    ("warning", "threshold", "pipeline_reliability", "Build success rate below 80%", "Review recent build failures and add retry logic for flaky steps"),
    ("warning", "threshold", "security_governance", "Security compliance below 70%", "Enable cluster policies and review credential exposure"),
    ("info", "milestone", "data_quality", "Data quality improved by 15% this quarter", "Continue expanding DLT expectations coverage"),
    ("critical", "anomaly", "cost_efficiency", "Compute cost anomaly: 3x spike in interactive usage", "Review long-running interactive clusters and migrate to job clusters"),
    ("warning", "trend", "environment_promotion", "Staging promotion rate declining", "Ensure staging deployment gates are not blocking valid promotions"),
    ("info", "milestone", "pipeline_reliability", "Pipeline reliability reached Elite tier", "Consider sharing your pipeline template as a golden path reference"),
]

alert_rows = []
for team_id in team_profiles:
    n_alerts = random.randint(2, 5)
    for alert in random.sample(alert_templates, n_alerts):
        severity, atype, domain, msg, rec = alert
        d = base_date + timedelta(days=random.randint(0, 89))
        alert_rows.append((
            str(uuid.uuid4()), team_id, d,
            severity, atype, domain, msg, rec,
            random.choice([True, False])
        ))

df_alerts = spark.createDataFrame(alert_rows, [
    "alert_id", "team_id", "created_date", "severity", "alert_type",
    "domain", "message", "recommendation", "is_acknowledged"
])
df_alerts.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.coaching_alerts")
print(f"  Loaded {df_alerts.count()} coaching alerts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## External Quality Metrics (Jira/ADO signals)

# COMMAND ----------

ext_rows = []
event_types = ["incident", "defect", "pull_request", "deployment"]
priorities = ["Critical", "Major", "Minor", "Trivial"]

for team_id in team_profiles:
    for _ in range(random.randint(30, 80)):
        d = base_date + timedelta(days=random.randint(0, 89))
        src = random.choice(["jira", "azure_devops"])
        etype = random.choice(event_types)
        ext_rows.append((
            str(uuid.uuid4()), team_id, src, etype, d,
            f"{'INC' if etype == 'incident' else 'DEF' if etype == 'defect' else 'PR' if etype == 'pull_request' else 'DEP'}-{random.randint(1000,9999)}",
            random.choice(["open", "resolved", "closed", "in_progress"]),
            random.choice(priorities),
            "{}"
        ))

df_ext = spark.createDataFrame(ext_rows, [
    "metric_id", "team_id", "source_system", "event_type", "event_date",
    "title", "status", "priority", "metadata"
])
df_ext.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.external_quality_metrics")
print(f"  Loaded {df_ext.count()} external quality metrics")

# COMMAND ----------

# MAGIC %md
# MAGIC ## DORA Metrics (scored)

# COMMAND ----------

dora_rows = []
dora_profiles = {
    "team_001": {"df": 5.0, "lt": 4.0, "cfr": 0.04, "rt": 2.0, "rw": 0.05},
    "team_002": {"df": 2.0, "lt": 12.0, "cfr": 0.08, "rt": 8.0, "rw": 0.10},
    "team_003": {"df": 0.5, "lt": 48.0, "cfr": 0.12, "rt": 24.0, "rw": 0.15},
    "team_004": {"df": 0.2, "lt": 96.0, "cfr": 0.18, "rt": 72.0, "rw": 0.20},
    "team_005": {"df": 3.0, "lt": 8.0, "cfr": 0.03, "rt": 1.5, "rw": 0.03},
}

def classify_dora_tier(df, lt, cfr, rt):
    tiers = []
    tiers.append("Elite" if df >= 1.0 else "High" if df >= 0.143 else "Medium" if df >= 0.033 else "Low")
    tiers.append("Elite" if lt <= 1 else "High" if lt <= 24 else "Medium" if lt <= 168 else "Low")
    tiers.append("Elite" if cfr <= 0.05 else "High" if cfr <= 0.10 else "Medium" if cfr <= 0.15 else "Low")
    tiers.append("Elite" if rt <= 1 else "High" if rt <= 24 else "Medium" if rt <= 168 else "Low")
    return tiers + [min(tiers, key=lambda x: ["Elite", "High", "Medium", "Low"].index(x))]

for team_id, dp in dora_profiles.items():
    ts = classify_dora_tier(dp["df"], dp["lt"], dp["cfr"], dp["rt"])
    dora_rows.append((
        str(uuid.uuid4()), team_id,
        dp["df"], dp["lt"], dp["cfr"], dp["rt"], dp["rw"],
        ts[0], ts[1], ts[2], ts[3], ts[4],
        datetime(2026, 3, 27, 12, 0, 0)
    ))

df_dora = spark.createDataFrame(dora_rows, [
    "record_id", "team_id", "deployment_frequency", "lead_time_hours",
    "change_failure_rate", "recovery_time_hours", "rework_rate",
    "df_tier", "lt_tier", "cfr_tier", "rt_tier", "overall_tier", "scored_at"
])
df_dora.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.scored_dora_metrics")
print(f"  Loaded {df_dora.count()} DORA metric records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compass Composite Scores

# COMMAND ----------

import json

composite_rows = []
archetypes = {
    "team_001": "Harmonious High-Achievers",
    "team_002": "Throughput Champions",
    "team_003": "Steady Improvers",
    "team_004": "Foundational Challenges",
    "team_005": "Stability Guardians",
}

for team_id, profile in team_profiles.items():
    composite = sum(profile[d] * weights[d] for d in domains)
    level = 1 if composite < 21 else 2 if composite < 41 else 3 if composite < 61 else 4 if composite < 81 else 5
    label = ["", "Initial", "Managed", "Defined", "Optimized", "Elite"][level]
    dim_json = json.dumps({d: {"score": profile[d], "weight": weights[d]} for d in domains})

    composite_rows.append((
        str(uuid.uuid4()), team_id,
        round(composite, 2), level, label,
        archetypes[team_id], dim_json,
        datetime(2026, 3, 27, 12, 0, 0)
    ))

df_composite = spark.createDataFrame(composite_rows, [
    "record_id", "team_id", "composite_score", "maturity_level",
    "maturity_label", "archetype", "dimension_json", "scored_at"
])
df_composite.write.mode("overwrite").saveAsTable(f"{catalog}.{schema}.scored_compass_composite")
print(f"  Loaded {df_composite.count()} composite score records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
print(f"\n{'='*60}")
print(f"Synthetic data loaded into {catalog}.{schema}")
print(f"{'='*60}")
for t in sorted(tables, key=lambda r: r.tableName):
    try:
        count = spark.table(f"{catalog}.{schema}.{t.tableName}").count()
        print(f"  {t.tableName:40s} {count:>8,} rows")
    except Exception:
        print(f"  {t.tableName:40s}     empty")
print(f"{'='*60}")
