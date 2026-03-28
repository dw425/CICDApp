#!/bin/bash
# Load synthetic data into lho_ucm.cicd tables via SQL Statements API
PROFILE="planxs"
WH="0c5bd90f54a5bd8b"
C="lho_ucm"
S="cicd"

run_sql() {
    local stmt="$1"
    local name="$2"
    result=$(databricks --profile $PROFILE api post /api/2.0/sql/statements \
        --json "{\"warehouse_id\": \"$WH\", \"statement\": $(python3 -c "import json; print(json.dumps('$stmt'.replace(\"'\", \"''\")))" 2>/dev/null || echo "\"$stmt\""), \"wait_timeout\": \"60s\"}" 2>&1)
    state=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status']['state'])" 2>/dev/null)
    if [ "$state" = "SUCCEEDED" ]; then
        echo "  OK: $name"
    else
        err=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'].get('error',{}).get('message','unknown')[:200])" 2>/dev/null)
        echo "  FAIL: $name - $err"
    fi
}

echo "Loading synthetic data into $C.$S..."
echo ""

# Teams
echo "=== Teams ==="
run_sql "INSERT INTO $C.$S.team_registry VALUES ('team_001', 'Platform Engineering', 12, '2024-01-15'), ('team_002', 'Data Engineering', 8, '2024-01-15'), ('team_003', 'ML Ops', 6, '2024-02-01'), ('team_004', 'Application Dev', 15, '2024-02-15'), ('team_005', 'Security and Compliance', 5, '2024-03-01')" "team_registry (5 teams)"

# DORA Metrics
echo ""
echo "=== DORA Metrics ==="
run_sql "INSERT INTO $C.$S.scored_dora_metrics VALUES ('d001', 'team_001', 5.0, 4.0, 0.04, 2.0, 0.05, 'Elite', 'Elite', 'Elite', 'Elite', 'Elite', current_timestamp()), ('d002', 'team_002', 2.0, 12.0, 0.08, 8.0, 0.10, 'Elite', 'High', 'High', 'High', 'High', current_timestamp()), ('d003', 'team_003', 0.5, 48.0, 0.12, 24.0, 0.15, 'Elite', 'Medium', 'Medium', 'Medium', 'Medium', current_timestamp()), ('d004', 'team_004', 0.2, 96.0, 0.18, 72.0, 0.20, 'High', 'Medium', 'Low', 'Medium', 'Low', current_timestamp()), ('d005', 'team_005', 3.0, 8.0, 0.03, 1.5, 0.03, 'Elite', 'High', 'Elite', 'Elite', 'Elite', current_timestamp())" "scored_dora_metrics (5 teams)"

# Compass Composite Scores
echo ""
echo "=== Compass Composite ==="
run_sql "INSERT INTO $C.$S.scored_compass_composite VALUES ('c001', 'team_001', 81.25, 5, 'Elite', 'Harmonious High-Achievers', '{\"golden_path\":{\"score\":82,\"weight\":0.25},\"environment_promotion\":{\"score\":78,\"weight\":0.15},\"pipeline_reliability\":{\"score\":88,\"weight\":0.20},\"data_quality\":{\"score\":75,\"weight\":0.15},\"security_governance\":{\"score\":85,\"weight\":0.15},\"cost_efficiency\":{\"score\":70,\"weight\":0.10}}', current_timestamp()), ('c002', 'team_002', 69.75, 4, 'Optimized', 'Throughput Champions', '{\"golden_path\":{\"score\":65,\"weight\":0.25},\"environment_promotion\":{\"score\":72,\"weight\":0.15},\"pipeline_reliability\":{\"score\":70,\"weight\":0.20},\"data_quality\":{\"score\":85,\"weight\":0.15},\"security_governance\":{\"score\":60,\"weight\":0.15},\"cost_efficiency\":{\"score\":75,\"weight\":0.10}}', current_timestamp()), ('c003', 'team_003', 53.75, 3, 'Defined', 'Steady Improvers', '{\"golden_path\":{\"score\":50,\"weight\":0.25},\"environment_promotion\":{\"score\":55,\"weight\":0.15},\"pipeline_reliability\":{\"score\":60,\"weight\":0.20},\"data_quality\":{\"score\":70,\"weight\":0.15},\"security_governance\":{\"score\":45,\"weight\":0.15},\"cost_efficiency\":{\"score\":55,\"weight\":0.10}}', current_timestamp()), ('c004', 'team_004', 40.75, 2, 'Managed', 'Foundational Challenges', '{\"golden_path\":{\"score\":35,\"weight\":0.25},\"environment_promotion\":{\"score\":40,\"weight\":0.15},\"pipeline_reliability\":{\"score\":55,\"weight\":0.20},\"data_quality\":{\"score\":45,\"weight\":0.15},\"security_governance\":{\"score\":30,\"weight\":0.15},\"cost_efficiency\":{\"score\":50,\"weight\":0.10}}', current_timestamp()), ('c005', 'team_005', 80.15, 4, 'Optimized', 'Stability Guardians', '{\"golden_path\":{\"score\":88,\"weight\":0.25},\"environment_promotion\":{\"score\":80,\"weight\":0.15},\"pipeline_reliability\":{\"score\":75,\"weight\":0.20},\"data_quality\":{\"score\":70,\"weight\":0.15},\"security_governance\":{\"score\":92,\"weight\":0.15},\"cost_efficiency\":{\"score\":65,\"weight\":0.10}}', current_timestamp())" "scored_compass_composite (5 teams)"

# Coaching Alerts
echo ""
echo "=== Coaching Alerts ==="
run_sql "INSERT INTO $C.$S.coaching_alerts VALUES ('a001', 'team_004', '2026-03-15', 'critical', 'regression', 'golden_path', 'Golden path adoption dropped below 50%', 'Investigate recent manual deployments and enforce SPN-based CI/CD', false), ('a002', 'team_004', '2026-03-10', 'warning', 'threshold', 'pipeline_reliability', 'Build success rate below 80%', 'Review recent build failures and add retry logic for flaky steps', false), ('a003', 'team_003', '2026-03-12', 'warning', 'threshold', 'security_governance', 'Security compliance below 70%', 'Enable cluster policies and review credential exposure', true), ('a004', 'team_001', '2026-03-20', 'info', 'milestone', 'pipeline_reliability', 'Pipeline reliability reached Elite tier', 'Consider sharing your pipeline template as a golden path reference', true), ('a005', 'team_002', '2026-03-18', 'warning', 'trend', 'environment_promotion', 'Staging promotion rate declining', 'Ensure staging deployment gates are not blocking valid promotions', false), ('a006', 'team_003', '2026-03-25', 'critical', 'anomaly', 'cost_efficiency', 'Compute cost anomaly: 3x spike in interactive usage', 'Review long-running interactive clusters and migrate to job clusters', false), ('a007', 'team_005', '2026-03-22', 'info', 'milestone', 'security_governance', 'Security compliance exceeded 90%', 'Maintain compliance posture and document audit trail', true)" "coaching_alerts (7 alerts)"

echo ""
echo "=== Verifying row counts ==="
for table in team_registry deployment_events maturity_scores maturity_trends coaching_alerts external_quality_metrics scored_dora_metrics scored_compass_composite scored_hygiene_checks scored_dimension_telemetry scored_hybrid_scores data_source_configs; do
    result=$(databricks --profile $PROFILE api post /api/2.0/sql/statements \
        --json "{\"warehouse_id\": \"$WH\", \"statement\": \"SELECT count(*) as cnt FROM $C.$S.$table\", \"wait_timeout\": \"30s\"}" 2>&1)
    cnt=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('data_array',[[0]])[0][0])" 2>/dev/null)
    printf "  %-40s %s rows\n" "$table" "$cnt"
done
