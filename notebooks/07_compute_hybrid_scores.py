# Databricks notebook source
# MAGIC %md
# MAGIC # Compute Hybrid Scores
# MAGIC Reads from scored_hygiene_checks (telemetry) and assessment store (questionnaire),
# MAGIC runs hybrid_scoring.compute_hybrid_score() per dimension,
# MAGIC writes to cicd_scored.scored_hybrid_scores.

# COMMAND ----------

from datetime import datetime

from config.settings import get_full_table_name
from compass.hybrid_scoring import compute_hybrid_score
from compass.scoring_engine import score_all_dimensions

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Read telemetry scores from scored_dimension_telemetry

# COMMAND ----------

def load_telemetry_scores(spark, team_id):
    """Load latest telemetry scores per dimension."""
    target = get_full_table_name("scored_dimension_telemetry")
    try:
        df = spark.sql(f"""
            SELECT dimension, telemetry_score, hard_gate_triggered
            FROM {target}
            WHERE team_id = '{team_id}'
            ORDER BY scored_at DESC
        """)
        rows = df.collect()
        return {r["dimension"]: {
            "telemetry_score": r["telemetry_score"],
            "hard_gate_triggered": r["hard_gate_triggered"],
        } for r in rows}
    except Exception:
        return {}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Read assessment scores from latest compass assessment

# COMMAND ----------

def load_assessment_scores(spark, team_id):
    """Load the latest questionnaire scores for a team.
    Falls back to the assessment_store JSON if no scored table exists."""
    try:
        from compass.assessment_store import list_assessments
        assessments = list_assessments()
        if not assessments:
            return {}
        latest = sorted(assessments, key=lambda a: a.get("completed_at", ""), reverse=True)[0]
        responses = latest.get("responses", {})
        uses_db = latest.get("uses_databricks", False)
        dim_scores = score_all_dimensions(responses, uses_databricks=uses_db)
        return {dim_id: data.get("raw_score", 0) for dim_id, data in dim_scores.items()}
    except Exception:
        return {}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Compute hybrid blend per dimension

# COMMAND ----------

def compute_all_hybrid_scores(telemetry_scores, assessment_scores):
    """Compute hybrid 70/30 blend for each dimension."""
    all_dims = set(list(telemetry_scores.keys()) + list(assessment_scores.keys()))
    results = {}
    for dim_id in all_dims:
        if "." in dim_id:
            continue
        tel = telemetry_scores.get(dim_id, {})
        tel_score = tel.get("telemetry_score")
        assess_score = assessment_scores.get(dim_id)
        hybrid = compute_hybrid_score(
            telemetry_score=tel_score,
            assessment_score=assess_score,
        )
        results[dim_id] = hybrid
    return results

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Write hybrid scores to Delta

# COMMAND ----------

def write_hybrid_scores(spark, team_id, hybrid_results):
    """Write hybrid scores to scored_hybrid_scores table."""
    scored_at = datetime.utcnow().isoformat()
    rows = []
    for dim_id, result in hybrid_results.items():
        rows.append({
            "team_id": team_id,
            "dimension": dim_id,
            "hybrid_score": result.get("hybrid_score", 0),
            "telemetry_score": result.get("telemetry_score"),
            "assessment_score": result.get("assessment_score"),
            "confidence": result.get("confidence", "none"),
            "discrepancy_delta": result.get("discrepancy_delta", 0),
            "scored_at": scored_at,
        })

    if rows:
        target = get_full_table_name("scored_hybrid_scores")
        df = spark.createDataFrame(rows)
        df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
        print(f"Wrote {len(rows)} hybrid scores to {target}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Main execution

# COMMAND ----------

try:
    team_id = dbutils.widgets.get("team_id")
except Exception:
    team_id = "default_team"

print(f"Computing hybrid scores for team: {team_id}")
telemetry = load_telemetry_scores(spark, team_id)
assessment = load_assessment_scores(spark, team_id)
hybrid = compute_all_hybrid_scores(telemetry, assessment)
write_hybrid_scores(spark, team_id, hybrid)
print(f"Hybrid scoring complete: {len(hybrid)} dimensions scored")
