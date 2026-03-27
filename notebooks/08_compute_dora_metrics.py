# Databricks notebook source
# MAGIC %md
# MAGIC # Compute DORA Metrics
# MAGIC Reads from cicd_normalized.pipeline_executions, code_changes, deployments, incidents.
# MAGIC Runs dora_calculator.compute_dora_metrics().
# MAGIC Writes to cicd_scored.scored_dora_metrics.

# COMMAND ----------

from datetime import datetime, timedelta

from config.settings import get_full_table_name
from compass.dora_calculator import compute_dora_metrics

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read normalized data for DORA calculation

# COMMAND ----------

def load_dora_source_data(spark, team_id, period_days=30):
    """Load normalized pipeline, deployment, code change, and incident data."""
    cutoff = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    data = {}

    # Deployments
    try:
        deploy_table = get_full_table_name("normalized_deployments")
        deploys = spark.sql(f"""
            SELECT * FROM {deploy_table}
            WHERE team_id = '{team_id}'
              AND deployed_at >= '{cutoff}'
        """).collect()
        data["deployments"] = [r.asDict() for r in deploys]
    except Exception:
        data["deployments"] = []

    # Code changes (PRs/MRs)
    try:
        changes_table = get_full_table_name("normalized_code_changes")
        changes = spark.sql(f"""
            SELECT * FROM {changes_table}
            WHERE team_id = '{team_id}'
              AND created_at >= '{cutoff}'
        """).collect()
        data["code_changes"] = [r.asDict() for r in changes]
    except Exception:
        data["code_changes"] = []

    # Pipeline executions
    try:
        pipeline_table = get_full_table_name("normalized_pipeline_executions")
        pipelines = spark.sql(f"""
            SELECT * FROM {pipeline_table}
            WHERE team_id = '{team_id}'
              AND started_at >= '{cutoff}'
        """).collect()
        data["pipeline_executions"] = [r.asDict() for r in pipelines]
    except Exception:
        data["pipeline_executions"] = []

    # Incidents
    try:
        incident_table = get_full_table_name("normalized_incidents")
        incidents = spark.sql(f"""
            SELECT * FROM {incident_table}
            WHERE team_id = '{team_id}'
              AND created_at >= '{cutoff}'
        """).collect()
        data["incidents"] = [r.asDict() for r in incidents]
    except Exception:
        data["incidents"] = []

    return data

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Compute DORA metrics from normalized data

# COMMAND ----------

def calculate_dora_from_normalized(source_data, period_days=30):
    """Calculate DORA metrics from normalized source data."""
    deployments = source_data.get("deployments", [])
    code_changes = source_data.get("code_changes", [])
    incidents = source_data.get("incidents", [])

    # Deployment Frequency
    deploy_count = len([d for d in deployments if d.get("environment") == "production"])
    deploy_freq = deploy_count / max(period_days, 1) if deploy_count else 0

    # Lead Time for Changes (median lead_time_hours from merged PRs)
    lead_times = [c["lead_time_hours"] for c in code_changes
                  if c.get("status") == "merged" and c.get("lead_time_hours")]
    median_lead_time = sorted(lead_times)[len(lead_times) // 2] if lead_times else None

    # Change Failure Rate
    total_deploys = len(deployments)
    failed_deploys = len([d for d in deployments if d.get("status") in ("failure", "rollback")])
    cfr = (failed_deploys / total_deploys * 100) if total_deploys > 0 else None

    # Mean Time to Recovery
    resolution_hours = [i["resolution_hours"] for i in incidents
                        if i.get("resolution_hours") and i.get("status") in ("resolved", "closed")]
    mttr = sum(resolution_hours) / len(resolution_hours) if resolution_hours else None

    # Reliability (inverse of incident rate)
    incident_rate = len(incidents) / max(period_days, 1)

    return {
        "deployment_frequency": deploy_freq,
        "lead_time_hours": median_lead_time,
        "change_failure_rate": cfr,
        "mttr_hours": mttr,
        "reliability_incident_rate": incident_rate,
        "period_days": period_days,
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Classify DORA tiers

# COMMAND ----------

def classify_dora_tier(metric_name, value):
    """Classify a DORA metric value into Elite/High/Medium/Low tier."""
    if value is None:
        return "Unknown"

    thresholds = {
        "deployment_frequency": [(1.0, "Elite"), (0.14, "High"), (0.033, "Medium"), (0, "Low")],
        "lead_time_hours": [(24, "Elite"), (168, "High"), (720, "Medium"), (float("inf"), "Low")],
        "change_failure_rate": [(5, "Elite"), (10, "High"), (15, "Medium"), (100, "Low")],
        "mttr_hours": [(1, "Elite"), (24, "High"), (168, "Medium"), (float("inf"), "Low")],
    }

    tiers = thresholds.get(metric_name, [])
    for threshold, tier in tiers:
        if metric_name in ("deployment_frequency",):
            if value >= threshold:
                return tier
        else:
            if value <= threshold:
                return tier
    return "Low"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Write DORA metrics to Delta

# COMMAND ----------

def write_dora_metrics(spark, team_id, dora_results, period_days):
    """Write DORA metric results to scored_dora_metrics table."""
    computed_at = datetime.utcnow().isoformat()
    unit_map = {
        "deployment_frequency": "deploys/day",
        "lead_time_hours": "hours",
        "change_failure_rate": "percent",
        "mttr_hours": "hours",
        "reliability_incident_rate": "incidents/day",
    }

    rows = []
    for metric_name in ["deployment_frequency", "lead_time_hours", "change_failure_rate",
                         "mttr_hours", "reliability_incident_rate"]:
        value = dora_results.get(metric_name)
        rows.append({
            "team_id": team_id,
            "metric_name": metric_name,
            "metric_value": float(value) if value is not None else None,
            "metric_unit": unit_map.get(metric_name, ""),
            "tier": classify_dora_tier(metric_name, value),
            "period_days": period_days,
            "computed_at": computed_at,
        })

    if rows:
        target = get_full_table_name("scored_dora_metrics")
        df = spark.createDataFrame(rows)
        df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
        print(f"Wrote {len(rows)} DORA metrics to {target}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Main execution

# COMMAND ----------

try:
    team_id = dbutils.widgets.get("team_id")
except Exception:
    team_id = "default_team"

try:
    period_days = int(dbutils.widgets.get("period_days"))
except Exception:
    period_days = 30

print(f"Computing DORA metrics for team: {team_id}, period: {period_days} days")
source_data = load_dora_source_data(spark, team_id, period_days)
dora_results = calculate_dora_from_normalized(source_data, period_days)
write_dora_metrics(spark, team_id, dora_results, period_days)

for k, v in dora_results.items():
    tier = classify_dora_tier(k, v)
    print(f"  {k}: {v} ({tier})")

print("DORA metrics computation complete")
