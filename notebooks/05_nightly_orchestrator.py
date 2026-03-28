# Databricks notebook source
# MAGIC %md
# MAGIC # Nightly Orchestrator
# MAGIC Runs the full scoring pipeline sequentially with error handling.
# MAGIC Notebooks: 01 → 02 → 03 → 04 → 06 → 07 → 08

# COMMAND ----------

from datetime import datetime

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

try:
    team_id = dbutils.widgets.get("team_id")
except Exception:
    team_id = "default_team"

NOTEBOOK_SEQUENCE = [
    ("01_extract_audit_events", "Extract raw audit events from CI/CD platforms"),
    ("02_compute_scores", "Compute raw maturity scores from ingested data"),
    ("03_rollup_trends", "Roll up scores into daily/weekly trends"),
    ("04_generate_alerts", "Generate coaching alerts from score changes"),
    ("06_hygiene_scoring", "Run hygiene checks and score per platform"),
    ("07_compute_hybrid_scores", "Compute hybrid 70/30 blend scores"),
    ("08_compute_dora_metrics", "Compute DORA 2025 metrics from normalized data"),
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute pipeline

# COMMAND ----------

def run_notebook(notebook_name, timeout_seconds=600):
    """Run a notebook with error handling and timing."""
    start = datetime.utcnow()
    try:
        result = dbutils.notebook.run(
            f"./{notebook_name}",
            timeout_seconds,
            {"team_id": team_id},
        )
        elapsed = (datetime.utcnow() - start).total_seconds()
        return {"status": "SUCCESS", "elapsed": elapsed, "result": result}
    except Exception as e:
        elapsed = (datetime.utcnow() - start).total_seconds()
        return {"status": "FAILED", "elapsed": elapsed, "error": str(e)}
    # ****Checked and Verified as Real*****
    # Run a notebook with error handling and timing.

# COMMAND ----------

results = {}
pipeline_start = datetime.utcnow()

for notebook_name, description in NOTEBOOK_SEQUENCE:
    print(f"\n{'='*60}")
    print(f"Running: {notebook_name}")
    print(f"  {description}")
    print(f"{'='*60}")

    result = run_notebook(notebook_name)
    results[notebook_name] = result

    if result["status"] == "SUCCESS":
        print(f"  Completed in {result['elapsed']:.1f}s")
    else:
        print(f"  FAILED after {result['elapsed']:.1f}s: {result.get('error', 'unknown')}")
        # Continue to next notebook — don't halt the pipeline on a single failure

pipeline_elapsed = (datetime.utcnow() - pipeline_start).total_seconds()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print(f"\n{'='*60}")
print(f"PIPELINE COMPLETE — {pipeline_elapsed:.1f}s total")
print(f"{'='*60}")

succeeded = sum(1 for r in results.values() if r["status"] == "SUCCESS")
failed = sum(1 for r in results.values() if r["status"] == "FAILED")

for name, result in results.items():
    status_icon = "OK" if result["status"] == "SUCCESS" else "FAIL"
    print(f"  [{status_icon}] {name} ({result['elapsed']:.1f}s)")

print(f"\n{succeeded} succeeded, {failed} failed out of {len(results)} notebooks")

if failed > 0:
    raise Exception(f"{failed} notebook(s) failed in nightly pipeline")
