# Databricks notebook source
# MAGIC %md
# MAGIC # Schema Bootstrap
# MAGIC Creates the catalog, schema, and all tables for CI/CD Maturity Intelligence.
# MAGIC Run this notebook once per environment to initialize the data model.

# COMMAND ----------

catalog = spark.conf.get("spark.databricks.catalog", "lho_analytics")
schema = "cicd"

print(f"Bootstrapping: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Catalog & Schema

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
spark.sql(f"USE SCHEMA {schema}")
print(f"Catalog and schema ready: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Custom Tables (7)

# COMMAND ----------

custom_ddl = {
    "team_registry": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.team_registry (
    team_id          STRING    NOT NULL,
    team_name        STRING    NOT NULL,
    member_count     INT,
    created_date     DATE
) USING DELTA
COMMENT 'Registry of engineering teams tracked by the CI/CD maturity app'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "deployment_events": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.deployment_events (
    event_id         STRING    NOT NULL,
    team_id          STRING    NOT NULL,
    event_date       DATE      NOT NULL,
    actor_type       STRING,
    actor_email      STRING,
    is_golden_path   BOOLEAN,
    artifact_type    STRING,
    environment      STRING,
    source_system    STRING,
    status           STRING
) USING DELTA
PARTITIONED BY (environment)
COMMENT 'Deployment events for golden-path and promotion scoring'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "maturity_scores": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.maturity_scores (
    score_id         STRING    NOT NULL,
    team_id          STRING    NOT NULL,
    score_date       DATE      NOT NULL,
    domain           STRING    NOT NULL,
    raw_score        DOUBLE,
    weighted_score   DOUBLE,
    composite_score  DOUBLE,
    maturity_tier    STRING
) USING DELTA
PARTITIONED BY (score_date)
COMMENT 'Daily per-team, per-domain maturity scores'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "maturity_trends": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.maturity_trends (
    trend_id         STRING    NOT NULL,
    team_id          STRING    NOT NULL,
    period_start     DATE      NOT NULL,
    period_end       DATE      NOT NULL,
    period_type      STRING    NOT NULL,
    avg_score        DOUBLE,
    min_score        DOUBLE,
    max_score        DOUBLE,
    delta            DOUBLE
) USING DELTA
PARTITIONED BY (period_type)
COMMENT 'Aggregated maturity trend rollups'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "coaching_alerts": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.coaching_alerts (
    alert_id         STRING    NOT NULL,
    team_id          STRING    NOT NULL,
    created_date     DATE      NOT NULL,
    severity         STRING    NOT NULL,
    alert_type       STRING,
    domain           STRING,
    message          STRING,
    recommendation   STRING,
    is_acknowledged  BOOLEAN
) USING DELTA
COMMENT 'Proactive coaching alerts from scoring engine'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "external_quality_metrics": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.external_quality_metrics (
    metric_id        STRING    NOT NULL,
    team_id          STRING    NOT NULL,
    source_system    STRING    NOT NULL,
    event_type       STRING    NOT NULL,
    event_date       DATE,
    title            STRING,
    status           STRING,
    priority         STRING,
    metadata         STRING
) USING DELTA
PARTITIONED BY (source_system)
COMMENT 'Quality signals from external systems (Jira, Azure DevOps)'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "data_source_configs": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.data_source_configs (
    config_id           STRING    NOT NULL,
    source_name         STRING    NOT NULL,
    source_type         STRING    NOT NULL,
    slot_id             STRING    NOT NULL,
    data_type           STRING,
    is_active           BOOLEAN,
    connection_config   STRING,
    field_mapping       STRING,
    filters             STRING,
    target_table        STRING,
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP,
    last_sync_at        TIMESTAMP,
    last_sync_status    STRING,
    last_sync_rows      INT
) USING DELTA
COMMENT 'Data source configurations for CI/CD wizard'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
}

for name, ddl in custom_ddl.items():
    spark.sql(ddl)
    print(f"  Created: {catalog}.{schema}.{name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scored Tables (5)

# COMMAND ----------

scored_ddl = {
    "scored_hygiene_checks": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.scored_hygiene_checks (
    check_id         STRING NOT NULL,
    team_id          STRING NOT NULL,
    platform         STRING NOT NULL,
    dimension        STRING NOT NULL,
    check_name       STRING,
    weight           DOUBLE,
    hard_gate        BOOLEAN,
    raw_value        STRING,
    score            DOUBLE,
    status           STRING,
    scored_at        TIMESTAMP
) USING DELTA
PARTITIONED BY (platform)
COMMENT 'Individual hygiene check scores (78 checks across 6 platforms)'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "scored_dimension_telemetry": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.scored_dimension_telemetry (
    record_id        STRING NOT NULL,
    team_id          STRING NOT NULL,
    dimension        STRING NOT NULL,
    score            DOUBLE,
    passing_count    INT,
    warning_count    INT,
    failing_count    INT,
    hard_gate_triggered BOOLEAN,
    scored_at        TIMESTAMP
) USING DELTA
COMMENT 'Aggregated dimension telemetry scores'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "scored_hybrid_scores": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.scored_hybrid_scores (
    record_id        STRING NOT NULL,
    team_id          STRING NOT NULL,
    dimension        STRING NOT NULL,
    telemetry_score  DOUBLE,
    assessment_score DOUBLE,
    blended_score    DOUBLE,
    confidence       STRING,
    flag             STRING,
    scored_at        TIMESTAMP
) USING DELTA
COMMENT 'Hybrid 70/30 blend of telemetry and assessment scores'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "scored_dora_metrics": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.scored_dora_metrics (
    record_id            STRING NOT NULL,
    team_id              STRING NOT NULL,
    deployment_frequency DOUBLE,
    lead_time_hours      DOUBLE,
    change_failure_rate  DOUBLE,
    recovery_time_hours  DOUBLE,
    rework_rate          DOUBLE,
    df_tier              STRING,
    lt_tier              STRING,
    cfr_tier             STRING,
    rt_tier              STRING,
    overall_tier         STRING,
    scored_at            TIMESTAMP
) USING DELTA
COMMENT 'DORA 2025 metrics with tier classification'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
    "scored_compass_composite": f"""
CREATE TABLE IF NOT EXISTS {catalog}.{schema}.scored_compass_composite (
    record_id        STRING NOT NULL,
    team_id          STRING NOT NULL,
    composite_score  DOUBLE,
    maturity_level   INT,
    maturity_label   STRING,
    archetype        STRING,
    dimension_json   STRING,
    scored_at        TIMESTAMP
) USING DELTA
COMMENT 'Top-level composite scores with archetype classification'
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
""",
}

for name, ddl in scored_ddl.items():
    spark.sql(ddl)
    print(f"  Created: {catalog}.{schema}.{name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify All Tables

# COMMAND ----------

tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
print(f"\nTotal tables created: {len(tables)}")
for t in sorted(tables, key=lambda r: r.tableName):
    print(f"  {t.tableName}")
