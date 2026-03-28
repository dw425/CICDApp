"""Load synthetic data into Databricks lakehouse tables via SQL Statements API."""

import json
import subprocess
import tempfile
import os
import uuid
import random
from datetime import date, timedelta

PROFILE = "planxs"
WH = "0c5bd90f54a5bd8b"
CATALOG = "lho_ucm"
SCHEMA = "cicd"


def run_sql(statement: str, label: str = "") -> bool:
    """Execute a SQL statement via Databricks SQL Statements API using temp file."""
    payload = {
        "warehouse_id": WH,
        "statement": statement,
        "wait_timeout": "50s",
    }
    # Write payload to temp file to avoid CLI arg length limits
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmppath = f.name

    try:
        result = subprocess.run(
            ["databricks", "--profile", PROFILE, "api", "post",
             "/api/2.0/sql/statements", "--json", f"@{tmppath}"],
            capture_output=True, text=True,
        )
        try:
            resp = json.loads(result.stdout)
            state = resp["status"]["state"]
            if state == "SUCCEEDED":
                rows = resp.get("result", {}).get("data_array", [[0]])[0]
                inserted = rows[1] if len(rows) > 1 else rows[0]
                print(f"  OK: {label} ({inserted} rows)")
                return True
            else:
                err = resp["status"].get("error", {}).get("message", "unknown")
                print(f"  FAIL: {label} - {err[:250]}")
                return False
        except Exception as e:
            print(f"  ERROR: {label} - {e}")
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}")
            return False
    finally:
        os.unlink(tmppath)


def main():
    random.seed(42)
    print(f"Loading synthetic data into {CATALOG}.{SCHEMA}...")

    # === Teams ===
    print("\n=== Teams ===")
    run_sql(f"""
        INSERT INTO {CATALOG}.{SCHEMA}.team_registry VALUES
        ('team_001', 'Platform Engineering', 12, DATE'2024-01-15'),
        ('team_002', 'Data Engineering', 8, DATE'2024-01-15'),
        ('team_003', 'ML Ops', 6, DATE'2024-02-01'),
        ('team_004', 'Application Dev', 15, DATE'2024-02-15'),
        ('team_005', 'Security and Compliance', 5, DATE'2024-03-01')
    """, "team_registry (5 teams)")

    # === Deployment Events ===
    print("\n=== Deployment Events ===")
    teams_config = {
        "team_001": (0.85, 8), "team_002": (0.70, 5), "team_003": (0.55, 3),
        "team_004": (0.40, 6), "team_005": (0.90, 2),
    }
    envs = ["dev", "staging", "prod"]
    artifacts = ["notebook", "job", "pipeline", "dlt_pipeline", "sql_query"]
    statuses = ["success", "success", "success", "success", "failed"]
    base = date(2026, 1, 1)

    for team_id, (gp_ratio, daily) in teams_config.items():
        values = []
        for day_offset in range(90):
            d = base + timedelta(days=day_offset)
            if d.weekday() >= 5:
                continue
            n = random.randint(max(1, daily - 2), daily + 2)
            for _ in range(n):
                is_gp = random.random() < gp_ratio
                actor = "service_principal" if is_gp else "human"
                email = "spn-cicd@corp.com" if is_gp else f"dev-{random.randint(1,20)}@corp.com"
                env = random.choice(envs)
                art = random.choice(artifacts)
                st = random.choice(statuses)
                eid = str(uuid.uuid4())[:8]
                values.append(
                    f"('{eid}', '{team_id}', DATE'{d}', '{actor}', '{email}', "
                    f"{'true' if is_gp else 'false'}, '{art}', '{env}', 'databricks', '{st}')"
                )

        # Insert in batches of 100
        for i in range(0, len(values), 100):
            batch = values[i:i+100]
            sql = f"INSERT INTO {CATALOG}.{SCHEMA}.deployment_events VALUES {', '.join(batch)}"
            run_sql(sql, f"deploy {team_id} batch {i//100+1} ({len(batch)} rows)")

    # === Maturity Scores ===
    print("\n=== Maturity Scores ===")
    domains = ["golden_path", "environment_promotion", "pipeline_reliability",
               "data_quality", "security_governance", "cost_efficiency"]
    weights = {"golden_path": 0.25, "environment_promotion": 0.15,
               "pipeline_reliability": 0.20, "data_quality": 0.15,
               "security_governance": 0.15, "cost_efficiency": 0.10}
    team_profiles = {
        "team_001": {"golden_path": 82, "environment_promotion": 78, "pipeline_reliability": 88, "data_quality": 75, "security_governance": 85, "cost_efficiency": 70},
        "team_002": {"golden_path": 65, "environment_promotion": 72, "pipeline_reliability": 70, "data_quality": 85, "security_governance": 60, "cost_efficiency": 75},
        "team_003": {"golden_path": 50, "environment_promotion": 55, "pipeline_reliability": 60, "data_quality": 70, "security_governance": 45, "cost_efficiency": 55},
        "team_004": {"golden_path": 35, "environment_promotion": 40, "pipeline_reliability": 55, "data_quality": 45, "security_governance": 30, "cost_efficiency": 50},
        "team_005": {"golden_path": 88, "environment_promotion": 80, "pipeline_reliability": 75, "data_quality": 70, "security_governance": 92, "cost_efficiency": 65},
    }

    for team_id, profile in team_profiles.items():
        values = []
        for day_offset in range(30):
            d = base + timedelta(days=day_offset + 60)
            trend = day_offset * 0.05
            for domain in domains:
                raw = max(0, min(100, round(profile[domain] + trend + random.gauss(0, 2), 2)))
                w = weights[domain]
                weighted = round(raw * w, 2)
                tier = "Initial" if raw < 21 else "Managed" if raw < 41 else "Defined" if raw < 61 else "Optimized" if raw < 81 else "Elite"
                sid = str(uuid.uuid4())[:8]
                values.append(
                    f"('{sid}', '{team_id}', DATE'{d}', '{domain}', "
                    f"{raw}, {weighted}, NULL, '{tier}')"
                )

        for i in range(0, len(values), 100):
            batch = values[i:i+100]
            sql = f"INSERT INTO {CATALOG}.{SCHEMA}.maturity_scores VALUES {', '.join(batch)}"
            run_sql(sql, f"scores {team_id} batch {i//100+1} ({len(batch)} rows)")

    # === Maturity Trends ===
    print("\n=== Maturity Trends ===")
    trend_values = []
    for team_id, profile in team_profiles.items():
        base_composite = sum(profile[d] * weights[d] for d in domains)
        for week in range(13):
            start = base + timedelta(weeks=week)
            end = start + timedelta(days=6)
            trend_bonus = week * 0.3
            avg = round(base_composite + trend_bonus + random.gauss(0, 1.5), 2)
            mn = round(avg - random.uniform(1, 4), 2)
            mx = round(avg + random.uniform(1, 4), 2)
            delta = round(random.gauss(0.3, 1.0), 2) if week > 0 else 0
            tid = str(uuid.uuid4())[:8]
            trend_values.append(
                f"('{tid}', '{team_id}', DATE'{start}', DATE'{end}', 'weekly', "
                f"{avg}, {mn}, {mx}, {delta})"
            )

    sql = f"INSERT INTO {CATALOG}.{SCHEMA}.maturity_trends VALUES {', '.join(trend_values)}"
    run_sql(sql, f"maturity_trends ({len(trend_values)} rows)")

    # === Coaching Alerts ===
    print("\n=== Coaching Alerts ===")
    run_sql(f"""
        INSERT INTO {CATALOG}.{SCHEMA}.coaching_alerts VALUES
        ('a001', 'team_004', DATE'2026-03-15', 'critical', 'regression', 'golden_path', 'Golden path adoption dropped below 50 percent', 'Investigate recent manual deployments and enforce SPN-based CI/CD', false),
        ('a002', 'team_004', DATE'2026-03-10', 'warning', 'threshold', 'pipeline_reliability', 'Build success rate below 80 percent', 'Review recent build failures and add retry logic for flaky steps', false),
        ('a003', 'team_003', DATE'2026-03-12', 'warning', 'threshold', 'security_governance', 'Security compliance below 70 percent', 'Enable cluster policies and review credential exposure', true),
        ('a004', 'team_001', DATE'2026-03-20', 'info', 'milestone', 'pipeline_reliability', 'Pipeline reliability reached Elite tier', 'Consider sharing your pipeline template as a golden path reference', true),
        ('a005', 'team_002', DATE'2026-03-18', 'warning', 'trend', 'environment_promotion', 'Staging promotion rate declining', 'Ensure staging deployment gates are not blocking valid promotions', false),
        ('a006', 'team_003', DATE'2026-03-25', 'critical', 'anomaly', 'cost_efficiency', 'Compute cost anomaly: 3x spike in interactive usage', 'Review long-running interactive clusters and migrate to job clusters', false),
        ('a007', 'team_005', DATE'2026-03-22', 'info', 'milestone', 'security_governance', 'Security compliance exceeded 90 percent', 'Maintain compliance posture and document audit trail', true)
    """, "coaching_alerts (7 alerts)")

    # === External Quality Metrics ===
    print("\n=== External Quality Metrics ===")
    event_types = ["incident", "defect", "pull_request", "deployment"]
    priorities = ["Critical", "Major", "Minor", "Trivial"]
    sources = ["jira", "azure_devops"]

    ext_values = []
    for team_id in team_profiles:
        for _ in range(random.randint(15, 30)):
            d = base + timedelta(days=random.randint(0, 89))
            src = random.choice(sources)
            etype = random.choice(event_types)
            mid = str(uuid.uuid4())[:8]
            prefix = {"incident": "INC", "defect": "DEF", "pull_request": "PR", "deployment": "DEP"}[etype]
            title = f"{prefix}-{random.randint(1000,9999)}"
            status = random.choice(["open", "resolved", "closed", "in_progress"])
            priority = random.choice(priorities)
            ext_values.append(
                f"('{mid}', '{team_id}', '{src}', '{etype}', DATE'{d}', "
                f"'{title}', '{status}', '{priority}', '{{}}')"
            )

    sql = f"INSERT INTO {CATALOG}.{SCHEMA}.external_quality_metrics VALUES {', '.join(ext_values)}"
    run_sql(sql, f"external_quality_metrics ({len(ext_values)} rows)")

    # === DORA Metrics ===
    print("\n=== DORA Metrics ===")
    run_sql(f"""
        INSERT INTO {CATALOG}.{SCHEMA}.scored_dora_metrics VALUES
        ('d001', 'team_001', 5.0, 4.0, 0.04, 2.0, 0.05, 'Elite', 'Elite', 'Elite', 'Elite', 'Elite', current_timestamp()),
        ('d002', 'team_002', 2.0, 12.0, 0.08, 8.0, 0.10, 'Elite', 'High', 'High', 'High', 'High', current_timestamp()),
        ('d003', 'team_003', 0.5, 48.0, 0.12, 24.0, 0.15, 'Elite', 'Medium', 'Medium', 'Medium', 'Medium', current_timestamp()),
        ('d004', 'team_004', 0.2, 96.0, 0.18, 72.0, 0.20, 'High', 'Medium', 'Low', 'Medium', 'Low', current_timestamp()),
        ('d005', 'team_005', 3.0, 8.0, 0.03, 1.5, 0.03, 'Elite', 'High', 'Elite', 'Elite', 'Elite', current_timestamp())
    """, "scored_dora_metrics (5 teams)")

    # === Compass Composite ===
    print("\n=== Compass Composite ===")
    archetypes = {
        "team_001": ("81.25", "5", "Elite", "Harmonious High-Achievers"),
        "team_002": ("69.75", "4", "Optimized", "Throughput Champions"),
        "team_003": ("53.75", "3", "Defined", "Steady Improvers"),
        "team_004": ("40.75", "2", "Managed", "Foundational Challenges"),
        "team_005": ("80.15", "4", "Optimized", "Stability Guardians"),
    }

    comp_values = []
    for team_id, (score, level, label, arch) in archetypes.items():
        profile = team_profiles[team_id]
        dim_json = json.dumps({d: {"score": profile[d], "weight": weights[d]} for d in domains})
        # Escape single quotes for SQL
        dim_json_escaped = dim_json.replace("'", "''")
        comp_values.append(
            f"('{str(uuid.uuid4())[:8]}', '{team_id}', {score}, {level}, '{label}', "
            f"'{arch}', '{dim_json_escaped}', current_timestamp())"
        )

    sql = f"INSERT INTO {CATALOG}.{SCHEMA}.scored_compass_composite VALUES {', '.join(comp_values)}"
    run_sql(sql, f"scored_compass_composite (5 teams)")

    # === Verify ===
    print("\n" + "=" * 60)
    print("ROW COUNT VERIFICATION")
    print("=" * 60)
    tables = [
        "team_registry", "deployment_events", "maturity_scores", "maturity_trends",
        "coaching_alerts", "external_quality_metrics", "scored_dora_metrics",
        "scored_compass_composite",
    ]
    for table in tables:
        payload = json.dumps({
            "warehouse_id": WH,
            "statement": f"SELECT count(*) FROM {CATALOG}.{SCHEMA}.{table}",
            "wait_timeout": "30s",
        })
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(payload)
            tmppath = f.name
        result = subprocess.run(
            ["databricks", "--profile", PROFILE, "api", "post",
             "/api/2.0/sql/statements", "--json", f"@{tmppath}"],
            capture_output=True, text=True,
        )
        os.unlink(tmppath)
        try:
            resp = json.loads(result.stdout)
            cnt = resp.get("result", {}).get("data_array", [[0]])[0][0]
        except Exception:
            cnt = "?"
        print(f"  {table:40s} {str(cnt):>8} rows")

    print("=" * 60)
    print("Synthetic data load complete!")


if __name__ == "__main__":
    main()
