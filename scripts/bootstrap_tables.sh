#!/bin/bash
# Bootstrap all tables in lho_ucm.cicd via Databricks SQL Statements API
PROFILE="planxs"
WH="0c5bd90f54a5bd8b"
CATALOG="lho_ucm"
SCHEMA="cicd"

run_sql() {
    local stmt="$1"
    local name="$2"
    result=$(databricks --profile $PROFILE api post /api/2.0/sql/statements \
        --json "{\"warehouse_id\": \"$WH\", \"statement\": \"$stmt\", \"wait_timeout\": \"30s\"}" 2>&1)
    state=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status']['state'])" 2>/dev/null)
    if [ "$state" = "SUCCEEDED" ]; then
        echo "  OK: $name"
    else
        err=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'].get('error',{}).get('message','unknown'))" 2>/dev/null)
        echo "  FAIL: $name - $err"
    fi
}

echo "Creating tables in $CATALOG.$SCHEMA..."

# Custom tables
run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.team_registry (team_id STRING NOT NULL, team_name STRING NOT NULL, member_count INT, created_date DATE) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "team_registry"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.deployment_events (event_id STRING NOT NULL, team_id STRING NOT NULL, event_date DATE NOT NULL, actor_type STRING, actor_email STRING, is_golden_path BOOLEAN, artifact_type STRING, environment STRING, source_system STRING, status STRING) USING DELTA PARTITIONED BY (environment) TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "deployment_events"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.maturity_scores (score_id STRING NOT NULL, team_id STRING NOT NULL, score_date DATE NOT NULL, domain STRING NOT NULL, raw_score DOUBLE, weighted_score DOUBLE, composite_score DOUBLE, maturity_tier STRING) USING DELTA PARTITIONED BY (score_date) TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "maturity_scores"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.maturity_trends (trend_id STRING NOT NULL, team_id STRING NOT NULL, period_start DATE NOT NULL, period_end DATE NOT NULL, period_type STRING NOT NULL, avg_score DOUBLE, min_score DOUBLE, max_score DOUBLE, delta DOUBLE) USING DELTA PARTITIONED BY (period_type) TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "maturity_trends"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.coaching_alerts (alert_id STRING NOT NULL, team_id STRING NOT NULL, created_date DATE NOT NULL, severity STRING NOT NULL, alert_type STRING, domain STRING, message STRING, recommendation STRING, is_acknowledged BOOLEAN) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "coaching_alerts"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.external_quality_metrics (metric_id STRING NOT NULL, team_id STRING NOT NULL, source_system STRING NOT NULL, event_type STRING NOT NULL, event_date DATE, title STRING, status STRING, priority STRING, metadata STRING) USING DELTA PARTITIONED BY (source_system) TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "external_quality_metrics"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.data_source_configs (config_id STRING NOT NULL, source_name STRING NOT NULL, source_type STRING NOT NULL, slot_id STRING NOT NULL, data_type STRING, is_active BOOLEAN, connection_config STRING, field_mapping STRING, filters STRING, target_table STRING, created_at TIMESTAMP, updated_at TIMESTAMP, last_sync_at TIMESTAMP, last_sync_status STRING, last_sync_rows INT) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "data_source_configs"

# Scored tables
run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.scored_hygiene_checks (check_id STRING NOT NULL, team_id STRING NOT NULL, platform STRING NOT NULL, dimension STRING NOT NULL, check_name STRING, weight DOUBLE, hard_gate BOOLEAN, raw_value STRING, score DOUBLE, status STRING, scored_at TIMESTAMP) USING DELTA PARTITIONED BY (platform) TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "scored_hygiene_checks"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.scored_dimension_telemetry (record_id STRING NOT NULL, team_id STRING NOT NULL, dimension STRING NOT NULL, score DOUBLE, passing_count INT, warning_count INT, failing_count INT, hard_gate_triggered BOOLEAN, scored_at TIMESTAMP) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "scored_dimension_telemetry"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.scored_hybrid_scores (record_id STRING NOT NULL, team_id STRING NOT NULL, dimension STRING NOT NULL, telemetry_score DOUBLE, assessment_score DOUBLE, blended_score DOUBLE, confidence STRING, flag STRING, scored_at TIMESTAMP) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "scored_hybrid_scores"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.scored_dora_metrics (record_id STRING NOT NULL, team_id STRING NOT NULL, deployment_frequency DOUBLE, lead_time_hours DOUBLE, change_failure_rate DOUBLE, recovery_time_hours DOUBLE, rework_rate DOUBLE, df_tier STRING, lt_tier STRING, cfr_tier STRING, rt_tier STRING, overall_tier STRING, scored_at TIMESTAMP) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "scored_dora_metrics"

run_sql "CREATE TABLE IF NOT EXISTS $CATALOG.$SCHEMA.scored_compass_composite (record_id STRING NOT NULL, team_id STRING NOT NULL, composite_score DOUBLE, maturity_level INT, maturity_label STRING, archetype STRING, dimension_json STRING, scored_at TIMESTAMP) USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')" "scored_compass_composite"

# ---------------------------------------------------------------------------
# Grant permissions to App service principal
# ---------------------------------------------------------------------------
echo ""
APP_SP_ID="${APP_SERVICE_PRINCIPAL_ID:-}"

if [ -z "$APP_SP_ID" ]; then
    echo "SKIP: No APP_SERVICE_PRINCIPAL_ID set. To grant permissions, re-run with:"
    echo "  APP_SERVICE_PRINCIPAL_ID=<client-id> ./scripts/bootstrap_tables.sh"
    echo "  (Find the client ID in: Databricks UI → Compute → Apps → your app)"
else
    SP="\`$APP_SP_ID\`"
    echo "Granting permissions to service principal: $APP_SP_ID"

    echo "  App data grants ($CATALOG.$SCHEMA)..."
    run_sql "GRANT USE CATALOG ON CATALOG $CATALOG TO $SP" "USE CATALOG $CATALOG"
    run_sql "GRANT USE SCHEMA ON SCHEMA $CATALOG.$SCHEMA TO $SP" "USE SCHEMA $CATALOG.$SCHEMA"
    run_sql "GRANT SELECT ON SCHEMA $CATALOG.$SCHEMA TO $SP" "SELECT on $CATALOG.$SCHEMA"
    run_sql "GRANT MODIFY ON SCHEMA $CATALOG.$SCHEMA TO $SP" "MODIFY on $CATALOG.$SCHEMA"

    echo "  System table grants (requires admin)..."
    run_sql "GRANT USE CATALOG ON CATALOG system TO $SP" "USE CATALOG system"
    for SYS_SCHEMA in system.access system.lakeflow system.billing system.compute system.information_schema system.query; do
        run_sql "GRANT USE SCHEMA ON SCHEMA $SYS_SCHEMA TO $SP" "USE SCHEMA $SYS_SCHEMA"
        run_sql "GRANT SELECT ON SCHEMA $SYS_SCHEMA TO $SP" "SELECT on $SYS_SCHEMA"
    done
fi

echo ""
echo "Verifying tables..."
databricks --profile $PROFILE api post /api/2.0/sql/statements \
    --json "{\"warehouse_id\": \"$WH\", \"statement\": \"SHOW TABLES IN $CATALOG.$SCHEMA\", \"wait_timeout\": \"30s\"}" 2>&1 \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['status']['state'] == 'SUCCEEDED':
    rows = d.get('result',{}).get('data_array',[])
    print(f'Total tables: {len(rows)}')
    for r in sorted(rows):
        print(f'  {r[1]}')
else:
    print('Failed to list tables:', d['status'].get('error',{}).get('message',''))
"
