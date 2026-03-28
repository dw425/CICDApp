# PIPELINE COMPASS v3 — Comprehensive Implementation Plan

> **Date:** 2026-03-27
> **Status:** DRAFT — Synthesized from 10 source documents + full codebase audit
> **Purpose:** Close every gap between the current app and what the research, specs, and customer requirements demand. Eliminate scaffold patterns. Produce production-grade, deployable code.

---

## PART 1: HONEST STATE OF THE WORLD

### What EXISTS and WORKS Today (v2.1 — commit 9818890)

| Area | Status | Evidence |
|------|--------|----------|
| **16 UI pages** | Functional in mock mode | All render, all have callbacks, 100+ Dash callbacks wired |
| **6 API connectors** | Code complete, mock-tested | GitHub (700L), GitLab (708L), Jenkins (494L), ADO (670L), Jira (336L), Databricks (702L) |
| **78 hygiene checks** | Real scoring rules | 6 platform extractors, hard gates, weighted aggregation |
| **Scoring engine** | Real algorithms | Weighted geometric mean, 5 weight profiles, adaptive skip logic |
| **Hybrid scoring** | Real blending | 70/30 telemetry/assessment, discrepancy detection |
| **DORA calculator** | 5 real metrics | Deploy freq, lead time, CFR, MTTR, rework rate — all computed from DataFrames |
| **Assessment wizard** | 200+ questions | 14 YAML files, adaptive branching, "I Don't Know" support |
| **Roadmap engine** | 50+ improvement items | Gap-based filtering, impact/effort matrix, phased timelines |
| **PDF/PPTX export** | Functional | WeasyPrint + python-pptx, branded templates |
| **52 tests** | All passing | Scoring, hygiene, DORA, hard gates, persistence, hybrid blend |
| **20 mock CSVs** | Realistic data | Teams, deployments, pipeline runs, hygiene scores, DORA metrics |

### What is SCAFFOLD — Code Exists but Has Never Run Against Real Systems

These are the hard truths. The code is syntactically complete but has **zero production validation**:

| Component | The Problem | Why It Matters |
|-----------|-------------|----------------|
| **All 6 connectors in live mode** | `fetch_repo_hygiene()` has never been called against a real GitHub/GitLab/Jenkins/ADO/Jira API. Every `if self.use_mock: return self._mock_*()` path has been tested; the `else` branch has not. | A customer connecting real credentials will hit untested code paths: pagination, rate limiting, auth token refresh, 404 handling, API version mismatches |
| **Databricks system table queries** | `data_layer/queries/system_tables.py` has SQL strings for `system.access.audit`, `system.lakeflow.jobs`, `system.compute.clusters`, etc. None have been executed against a real Databricks workspace. | The entire golden-path detection logic depends on these queries working correctly |
| **Delta Lake DDL** | `raw_ddl.py`, `normalized_ddl.py`, `scored_ddl.py` define 15+ CREATE TABLE statements. None have been executed. | The Lakehouse data model is theoretical |
| **Notebooks 05-08** | Files exist with correct import paths and algorithm structure. Never been run in a Databricks workspace. | The nightly scoring pipeline that powers live dashboards is untested |
| **Connector → Extractor wiring** | `hygiene_scorer.run_all_checks()` calls extractors, which fall back to `_mock_*_data()`. The path where a connector's `fetch_repo_hygiene()` output flows into an extractor's `run_checks()` has been coded but not exercised end-to-end. | The bridge between "pull data from APIs" and "score that data" is the product's core value proposition — and it's never been run |
| **PDF/PPTX with DORA + hygiene** | `export_pdf.py` and `export_pptx.py` have DORA/hygiene sections coded but generate empty sections when no live telemetry exists | Client deliverables look incomplete without live data |

### What is COMPLETELY MISSING

These capabilities appear in the source documents but have zero code in the repo:

| Missing Capability | Source Document | Priority |
|-------------------|-----------------|----------|
| **Authentication / Authorization** | BUILD_PLAN (Auth0/Clerk SSO), Databricks App Spec (workspace auth) | P0 — blocking for any real deployment |
| **Golden Path deployment tagging** | Golden Path PDF — `golden_path_token` embedded in CI/CD pipeline metadata | P0 — the customer's original use case |
| **Webhook/real-time ingestion** | Databricks App Spec (Bronze layer Auto Loader from webhooks) | P1 — needed for live data |
| **Multi-tenant data isolation** | BUILD_PLAN (org_id scoping), Databricks App Spec | P1 — blocking for multi-customer |
| **Notification system** | Improvement Plan V2 (coaching alerts → Slack/Jira), Golden Path PDF | P1 |
| **Gamification / leaderboard** | Industry Research (Spotify Soundcheck medals, org-wide visibility), Golden Path PDF | P2 |
| **ROI calculator** | Databricks App Spec (C-Suite View), Industry Research (McKinsey DVI) | P2 |
| **Value stream mapping** | BUILD_PLAN (ValueStreamMap component), Industry Research | P2 |
| **PR cycle time analytics** | Industry Research (Cortex velocity dashboard), Databricks App Spec | P2 |
| **Flaky test detection** | Databricks App Spec (test flakiness rate), Industry Research | P3 |
| **ML-based predictive CI failure** | Databricks App Spec (AutoML), Industry Research | P3 |
| **LLM-generated remediation** | Databricks App Spec (Foundation Model APIs → draft runbooks) | P3 |
| **Docker Compose / containerization** | BUILD_PLAN | P1 |
| **CI/CD pipeline for the app itself** | Not in any doc — but required for dogfooding | P1 |
| **API layer (REST endpoints)** | BUILD_PLAN (FastAPI), needed for headless/CLI usage | P2 |
| **DX survey integration** | Industry Research (SPACE framework Satisfaction dimension) | P3 |

---

## PART 2: ARCHITECTURE DECISIONS

### Decision 1: Stay with Dash or Migrate to React/FastAPI?

The BUILD_PLAN specifies React 18 + TypeScript + FastAPI. The current app is Python Dash.

**Decision: STAY WITH DASH for v3. Add a FastAPI API layer alongside.**

Rationale:
- 16 pages, 100+ callbacks, 30+ components already working in Dash — rewrite cost is massive
- Dash is a valid Databricks App deployment target (Python-only, no Node build step)
- Adding FastAPI as a separate service provides REST API access without rewriting the UI
- The customer (Nationwide via Blueprint) needs a working product, not a tech stack migration

**Implementation:**
```
CICDApp/
├── app.py                    # Dash app (existing)
├── api/                      # NEW: FastAPI service
│   ├── main.py               # FastAPI app
│   ├── routes/
│   │   ├── assessments.py    # CRUD + submission
│   │   ├── scoring.py        # Score computation
│   │   ├── connectors.py     # Connector management
│   │   ├── hygiene.py        # Hygiene check results
│   │   ├── dora.py           # DORA metrics
│   │   └── export.py         # PDF/PPTX generation
│   └── auth.py               # OAuth2/JWT middleware
├── docker-compose.yml        # NEW: Container orchestration
├── Dockerfile                # NEW: App container
└── ...existing code...
```

### Decision 2: SQLite/JSON vs PostgreSQL

**Decision: Keep SQLite/JSON for Dash app (single-user/demo). Add PostgreSQL option for multi-tenant production.**

Implementation: Abstract the persistence layer behind a `StorageBackend` interface:
```python
class StorageBackend(Protocol):
    def save_assessment(self, assessment: dict) -> str: ...
    def get_assessment(self, assessment_id: str) -> dict | None: ...
    def list_assessments(self, org_id: str) -> list[dict]: ...
    # etc.

class JSONFileBackend(StorageBackend): ...     # Current implementation
class PostgresBackend(StorageBackend): ...     # New for production
class DatabricksBackend(StorageBackend): ...   # Future: Unity Catalog tables
```

### Decision 3: Deployment Target

**Decision: Support THREE deployment modes:**

| Mode | Target | Auth | Storage | Use Case |
|------|--------|------|---------|----------|
| **Local** | `python app.py` | None | SQLite/JSON | Development, demos |
| **Docker** | `docker compose up` | OAuth2 via FastAPI | PostgreSQL | Production (cloud) |
| **Databricks App** | Databricks workspace | Workspace auth | Unity Catalog tables | Customer-embedded |

---

## PART 3: THE v3 IMPLEMENTATION PLAN

### PHASE 0: Foundation — Production Hardening (Week 1-2)

> **Goal:** Make the existing code production-ready before adding features.

#### 0.1 End-to-End Connector Validation

**What:** Test every connector against real APIs. Fix every failure.

**For each connector (GitHub, GitLab, Jenkins, ADO, Jira, Databricks):**

1. **Create integration test suite** (`tests/integration/test_github_live.py`, etc.)
   - Requires real credentials via env vars (`GITHUB_TOKEN`, `GITLAB_TOKEN`, etc.)
   - Tests: authenticate → fetch_records → fetch_repo_hygiene → normalize → verify schema
   - Skipped in CI unless `RUN_INTEGRATION_TESTS=true`

2. **Fix real-world API issues:**
   - **Pagination:** All connectors have pagination code but it's never been stress-tested. Test with repos that have 1000+ PRs, 500+ workflow runs.
   - **Rate limiting:** GitHub (5000/hr), GitLab (300/min), Jenkins (no limit but slow), ADO (varies). Add exponential backoff with `tenacity` retry decorator.
   - **Error handling:** 404 for disabled features (code scanning not enabled), 403 for insufficient permissions, 401 for expired tokens. Each must return graceful fallback, not crash.
   - **Auth token refresh:** GitHub Apps use JWT → installation token flow with 1-hr expiry. Add token refresh logic.
   - **API version compatibility:** GitLab v4 features vary by edition (CE vs EE). ADO API versions differ across on-prem vs cloud. Add version detection.

3. **Add connection health check endpoint:**
   ```python
   def health_check(self) -> dict:
       """Returns {"status": "healthy|degraded|error", "latency_ms": int, "scopes": [...], "rate_limit_remaining": int}"""
   ```

4. **Wire the connector → extractor → scorer pipeline end-to-end:**
   - Create `ingestion/pipeline.py`:
     ```python
     def run_full_pipeline(connector_configs: list[dict]) -> dict:
         """
         For each configured connector:
         1. Authenticate
         2. Fetch repo hygiene data
         3. Pass to platform-specific extractor
         4. Run hygiene checks
         5. Aggregate dimension scores
         6. Compute hybrid blend with assessment scores
         7. Return unified score card
         """
     ```
   - **Acceptance test:** Configure GitHub connector with a real repo → run pipeline → verify scores are in 0-100 range and differ from mock data.

**Files to create/modify:**
- `tests/integration/test_github_live.py` (NEW)
- `tests/integration/test_gitlab_live.py` (NEW)
- `tests/integration/test_jenkins_live.py` (NEW)
- `tests/integration/test_ado_live.py` (NEW)
- `tests/integration/test_jira_live.py` (NEW)
- `tests/integration/test_databricks_live.py` (NEW)
- `tests/integration/conftest.py` (NEW — credential fixtures from env)
- `ingestion/pipeline.py` (NEW — end-to-end orchestration)
- All 6 connectors — add `tenacity` retry, health_check, error handling
- `compass/hygiene_scorer.py` — ensure `run_all_checks(connector_data=...)` works end-to-end

**Acceptance criteria:**
- [ ] Each connector can authenticate and fetch data from a real API (tested manually against at least one real instance)
- [ ] `ingestion/pipeline.py` runs end-to-end in mock mode AND live mode
- [ ] Rate limiting doesn't crash the app (test with GitHub rate limit simulation)
- [ ] Integration tests exist and are skippable in CI

#### 0.2 Databricks System Table Validation

**What:** Validate every SQL query in `data_layer/queries/system_tables.py` and `custom_tables.py` against a real Databricks workspace.

**Steps:**
1. Stand up a test workspace (or use existing)
2. Run each query from `system_tables.py`:
   - `get_audit_log_deployments()` → verify `system.access.audit` schema
   - `get_job_run_history()` → verify `system.lakeflow.job_run_timeline` schema
   - `get_job_definitions()` → verify `system.lakeflow.jobs` schema
   - `get_cluster_inventory()` → verify `system.compute.clusters` schema
   - `get_billing_usage()` → verify `system.billing.usage` schema
   - `get_uc_table_inventory()` → verify `system.information_schema.tables` schema
   - `get_dlt_expectations()` → verify DLT event log schema
   - `get_query_history()` → verify `system.query.history` schema
3. Fix any schema mismatches (column names, types, availability)
4. Add fallback queries for workspaces where certain system tables are disabled

**Files to modify:**
- `data_layer/queries/system_tables.py` — fix any schema issues
- `data_layer/connection.py` — add connection pooling, query timeout
- `tests/integration/test_databricks_queries.py` (NEW)

#### 0.3 Authentication Layer

**What:** Add authentication so the app can be deployed for real users.

**Implementation:**

For **Databricks App deployment** (primary target):
```python
# auth/databricks_auth.py
from databricks.sdk import WorkspaceClient

def get_current_user():
    """In Databricks App context, user identity comes from workspace auth."""
    w = WorkspaceClient()
    me = w.current_user.me()
    return {"email": me.user_name, "name": me.display_name, "groups": [g.display for g in me.groups]}
```

For **standalone deployment** (Docker):
```python
# auth/oauth.py
from authlib.integrations.starlette_client import OAuth

# Configure OAuth2 with Auth0/Entra ID
oauth = OAuth()
oauth.register("auth0", ...)
```

For **development** (no auth):
```python
# auth/dev_auth.py
def get_current_user():
    return {"email": "dev@local", "name": "Developer", "groups": ["admin"]}
```

**Dash integration:**
```python
# In app.py, wrap with auth middleware
from auth import get_auth_backend

auth = get_auth_backend(mode=os.environ.get("AUTH_MODE", "dev"))
# "dev" = no auth, "databricks" = workspace auth, "oauth" = OAuth2
```

**Files to create:**
- `auth/__init__.py` (NEW)
- `auth/databricks_auth.py` (NEW)
- `auth/oauth.py` (NEW)
- `auth/dev_auth.py` (NEW)
- `auth/middleware.py` (NEW — Dash middleware for auth checks)

#### 0.4 Containerization

**What:** Docker Compose for reproducible deployment.

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports: ["8060:8060"]
    environment:
      - AUTH_MODE=oauth
      - DATABASE_URL=postgresql://compass:compass@db:5432/compass
      - CICD_APP_USE_MOCK=false
    depends_on: [db]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: compass
      POSTGRES_USER: compass
      POSTGRES_PASSWORD: compass
    volumes: [pgdata:/var/lib/postgresql/data]

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports: ["8061:8061"]
    environment:
      - DATABASE_URL=postgresql://compass:compass@db:5432/compass
    depends_on: [db]

volumes:
  pgdata:
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8060
CMD ["python", "app.py"]
```

**Files to create:**
- `Dockerfile` (NEW)
- `Dockerfile.api` (NEW)
- `docker-compose.yml` (NEW)
- `.dockerignore` (NEW)
- `requirements.txt` — pin all dependency versions

#### 0.5 CI/CD Pipeline for the App Itself

**What:** GitHub Actions workflow to lint, test, build, and deploy.

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ -v --tb=short
      - run: python -m flake8 --max-line-length=120 --exclude=.git,__pycache__
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t pipeline-compass:${{ github.sha }} .
```

**Files to create:**
- `.github/workflows/ci.yml` (NEW)
- `.flake8` or `pyproject.toml` lint config (NEW)

---

### PHASE 1: Golden Path — The Customer's Core Use Case (Week 2-4)

> **Goal:** Deliver the Golden Path Deployment Adoption Tracking feature from the customer PDF. This is the #1 feature request.

#### 1.1 Golden Path Tagging Mechanism

**What:** A CI/CD pipeline component that injects a `golden_path_token` into deployment metadata, enabling the system to distinguish standard (pipeline-originated) deployments from non-standard (manual/ad-hoc) ones.

**Implementation:**

Create a reusable CI/CD template that teams embed in their pipelines:

```yaml
# templates/golden_path_tag.yml (GitHub Actions reusable workflow)
name: Golden Path Tag
on:
  workflow_call:
    inputs:
      artifact_type:
        required: true
        type: string  # notebook, app, ddl, job, pipeline, cluster, permission
    outputs:
      golden_path_token:
        value: ${{ jobs.tag.outputs.token }}

jobs:
  tag:
    runs-on: ubuntu-latest
    outputs:
      token: ${{ steps.generate.outputs.token }}
    steps:
      - id: generate
        run: |
          TOKEN=$(python3 -c "import uuid,json,base64,time; print(base64.b64encode(json.dumps({'pipeline_id':'${{ github.run_id }}','artifact_type':'${{ inputs.artifact_type }}','team':'${{ github.repository_owner }}','timestamp':time.time(),'sha':'${{ github.sha }}'}).encode()).decode())")
          echo "token=$TOKEN" >> $GITHUB_OUTPUT
```

Equivalent templates for:
- Azure DevOps (YAML pipeline task)
- GitLab CI (include template)
- Jenkins (shared library step)
- Databricks (DABs bundle metadata tag)

**Files to create:**
- `templates/github_golden_path.yml` (NEW)
- `templates/ado_golden_path.yml` (NEW)
- `templates/gitlab_golden_path.yml` (NEW)
- `templates/jenkins_golden_path.groovy` (NEW)
- `templates/databricks_golden_path.py` (NEW — DABs metadata injector)

#### 1.2 Event Capture & Classification Engine

**What:** Ingest ALL deployment events (from Databricks audit logs + CI/CD webhooks), classify each as standard vs non-standard, and store for analytics.

**Implementation:**

```python
# ingestion/golden_path_classifier.py

class GoldenPathClassifier:
    """Classifies deployment events as standard (golden path) or non-standard."""

    DEPLOYMENT_ACTIONS = {
        "createJob", "resetJob", "updateJob", "deleteJob",
        "import", "createNotebook", "updateNotebook",
        "createPipeline", "updatePipeline", "editPipeline",
        "createRepo", "updateRepo", "pull",
        "putSecretScope", "putSecret",
        "createCluster", "editCluster",
        "setPermissions", "updatePermissions",
    }

    def classify(self, event: dict) -> dict:
        """
        Classify a single deployment event.

        Returns: {
            "classification": "standard" | "non_standard" | "unknown",
            "confidence": float,  # 0-1
            "signals": list[str],  # why we classified this way
            "artifact_type": str,
            "team_id": str | None,
        }
        """
        signals = []

        # Signal 1: Service principal = likely CI/CD
        actor = event.get("user_identity", {}).get("email", "")
        is_sp = self._is_service_principal(actor)
        if is_sp:
            signals.append("service_principal_actor")

        # Signal 2: Golden path token in metadata
        has_token = self._has_golden_path_token(event)
        if has_token:
            signals.append("golden_path_token_present")

        # Signal 3: Source IP matches known CI/CD runners
        known_ci = self._is_known_ci_ip(event.get("source_ip_address"))
        if known_ci:
            signals.append("known_ci_runner_ip")

        # Signal 4: Git-backed source
        is_git = self._is_git_backed(event)
        if is_git:
            signals.append("git_backed_source")

        # Classification logic
        if has_token or (is_sp and is_git):
            classification = "standard"
            confidence = 0.95 if has_token else 0.85
        elif is_sp:
            classification = "standard"
            confidence = 0.70
        elif not is_sp and not has_token:
            classification = "non_standard"
            confidence = 0.90
        else:
            classification = "unknown"
            confidence = 0.50

        return {
            "classification": classification,
            "confidence": confidence,
            "signals": signals,
            "artifact_type": self._detect_artifact_type(event),
            "team_id": self._resolve_team(actor),
        }
```

**Files to create:**
- `ingestion/golden_path_classifier.py` (NEW)
- `data_layer/queries/golden_path_queries.py` (NEW — queries for adoption analytics)
- `tests/test_golden_path_classifier.py` (NEW)

#### 1.3 Golden Path Adoption Dashboard

**What:** New UI page showing adoption analytics per the customer's requirements.

**Visualizations:**
1. **Adoption pie chart** — % standard vs % non-standard deployments (org-wide)
2. **Team adoption heatmap** — Teams (rows) × Weeks (columns) → color by adoption %
3. **Non-standard drill-down table** — sortable list: timestamp, actor, artifact type, team, classification, confidence
4. **Trend line** — Golden path adoption % over time (daily/weekly/monthly)
5. **Artifact type breakdown** — Stacked bar: notebooks vs DDL vs jobs vs pipelines vs other, split by standard/non-standard
6. **Team leaderboard** — Ranked by adoption %, with success badges for >90% teams
7. **Coaching queue** — Teams below threshold with contact info and top violations

**Files to create:**
- `ui/pages/golden_path_adoption.py` (NEW)
- `callbacks/golden_path_callbacks.py` (NEW)
- `ui/components/adoption_pie.py` (NEW)
- `ui/components/team_heatmap.py` (NEW)
- `ui/components/leaderboard.py` (NEW)

**Files to modify:**
- `ui/sidebar.py` — Add Golden Path Adoption nav item
- `callbacks/navigation_callbacks.py` — Add page route

#### 1.4 Jira Defect Correlation

**What:** Correlate golden-path adoption with Jira defect rates. Teams using standard pipelines should have fewer defects — prove it with data.

**Implementation:**
- Pull Jira issues (bugs/incidents) per team per period
- Join with golden-path adoption % for same team/period
- Compute correlation coefficient
- Visualize as scatter plot: adoption % (x) vs defect rate (y)

**Files to modify:**
- `ingestion/api_connectors/jira.py` — Add `fetch_defect_counts(team_id, period)`
- `ui/pages/golden_path_adoption.py` — Add correlation section
- `callbacks/golden_path_callbacks.py` — Add correlation callback

---

### PHASE 2: Live Data Pipeline — Making Scores Real (Week 4-6)

> **Goal:** Replace mock data with real telemetry data flowing from CI/CD platforms through the scoring engine.

#### 2.1 Lakehouse Data Model Validation

**What:** Execute all DDL against a real Databricks workspace. Fix schema issues.

**Steps:**
1. Run `raw_ddl.py` DDL in a test workspace → fix any syntax/schema issues
2. Run `normalized_ddl.py` DDL → verify 6 canonical tables created
3. Run `scored_ddl.py` DDL → verify scored tables created
4. Populate with sample data from connectors
5. Run scoring queries against the data

**Expand DDL to cover all platforms fully (from FIX_PLAN Task 8):**

Raw tables needed (33 total):
- **GitHub (7):** github_workflow_runs, github_pull_requests, github_commits, github_repo_hygiene, github_repo_stats, github_deployments, github_security_alerts
- **ADO (7):** ado_builds, ado_pull_requests, ado_test_runs, ado_branch_policies, ado_releases, ado_work_items, ado_build_definitions
- **Jenkins (5):** jenkins_jobs, jenkins_builds, jenkins_job_configs, jenkins_test_reports, jenkins_plugins
- **GitLab (5):** gitlab_pipelines, gitlab_merge_requests, gitlab_dora_metrics, gitlab_vulnerabilities, gitlab_project_hygiene
- **Jira (2):** jira_issues, jira_issue_changelogs
- **Databricks (7):** databricks_job_inventory, databricks_cluster_inventory, databricks_audit_events, databricks_uc_tables, databricks_hive_tables, databricks_dlt_events, databricks_job_runs

**Files to modify:**
- `data_layer/queries/raw_ddl.py` — Expand to 33 tables with full column specs
- `data_layer/queries/normalized_ddl.py` — Add `repo_hygiene`, `test_executions` tables
- `data_layer/queries/scored_ddl.py` — Verify scored tables match scorer output

#### 2.2 Connector Sync Pipeline

**What:** Build the automated data sync pipeline that pulls from CI/CD platforms, normalizes, and loads into Lakehouse.

```python
# ingestion/sync_pipeline.py

class SyncPipeline:
    """Orchestrates data sync from configured connectors to Lakehouse."""

    def sync_all(self, connector_configs: list[dict]) -> SyncReport:
        """
        For each configured connector:
        1. Authenticate
        2. Determine last sync timestamp (incremental)
        3. Fetch new records since last sync
        4. Normalize to canonical schema
        5. Write to raw tables (append)
        6. Update normalized tables (merge/upsert)
        7. Log sync metadata
        """

    def sync_hygiene(self, connector_configs: list[dict]) -> HygieneReport:
        """
        For each configured connector:
        1. Call fetch_repo_hygiene()
        2. Pass to platform hygiene extractor
        3. Score all checks
        4. Write to scored_hygiene_checks table
        """
```

**Notebook update — `notebooks/05_nightly_orchestrator.py`:**
```python
# Nightly pipeline:
# 1. Sync raw data from all configured connectors
# 2. Run normalization transforms
# 3. Execute hygiene scoring (notebook 06)
# 4. Compute hybrid scores (notebook 07)
# 5. Compute DORA metrics (notebook 08)
# 6. Classify golden path deployments
# 7. Generate coaching alerts
# 8. Update maturity trends
```

**Files to create:**
- `ingestion/sync_pipeline.py` (NEW)
- `ingestion/sync_state.py` (NEW — tracks last sync per connector)

**Files to modify:**
- `notebooks/05_nightly_orchestrator.py` — Wire to sync pipeline
- `notebooks/06_hygiene_scoring.py` — Read from raw tables, write to scored
- `notebooks/07_compute_hybrid_scores.py` — Merge telemetry + assessment
- `notebooks/08_compute_dora_metrics.py` — Compute from normalized tables

#### 2.3 Data Sources Page Redesign

**What:** Transform the Data Sources page from a demo wizard into a real connector management console.

**Current state:** 6-step wizard that stores config but doesn't actually sync data.

**New design:**

```
┌─────────────────────────────────────────────────────┐
│ Connected Platforms                                  │
├──────────┬──────────┬──────┬────────┬───────────────┤
│ Platform │ Status   │ Last │ Health │ Actions       │
│          │          │ Sync │ Checks │               │
├──────────┼──────────┼──────┼────────┼───────────────┤
│ GitHub   │ ● Active │ 2h   │ 22/22  │ [Sync] [Edit]│
│ ADO      │ ● Active │ 6h   │ 13/13  │ [Sync] [Edit]│
│ Jenkins  │ ○ Error  │ 3d   │ 0/10   │ [Fix] [Edit] │
│ Databricks│● Active │ 1h   │ 13/13  │ [Sync] [Edit]│
└──────────┴──────────┴──────┴────────┴───────────────┘

[+ Add Platform]

┌─── Sync History ──────────────────────────────────┐
│ 2026-03-27 02:00 │ GitHub  │ 847 records │ 12.3s │
│ 2026-03-27 02:01 │ ADO     │ 234 records │  8.1s │
│ 2026-03-27 02:02 │ Databricks│1,203 records│ 4.2s │
│ 2026-03-26 14:00 │ Jenkins │ ERROR: 401  │  —    │
└───────────────────────────────────────────────────┘
```

**Files to modify:**
- `ui/pages/data_sources.py` — Redesign to management console
- `callbacks/datasource_callbacks.py` — Add sync trigger, health check, sync history callbacks
- `ui/components/wizard_steps.py` — Keep for "Add Platform" flow

---

### PHASE 3: Advanced Scoring & Intelligence (Week 6-8)

> **Goal:** Add the intelligence features that differentiate this product from basic dashboards.

#### 3.1 SPACE Framework Integration

**What:** Add Satisfaction & Well-being dimension alongside DORA metrics, per industry best practice (Microsoft Research + GitHub).

**Implementation:**
- Add a lightweight DX survey (5-7 questions) that teams can fill out periodically
- Questions based on DX Core 4: Speed, Effectiveness, Quality, Business Impact
- Store results and blend into scoring with a "developer experience" weight

**Survey questions (from industry research):**
```yaml
# compass/question_bank/dx_pulse.yaml
dimension: developer_experience_pulse
display_name: "Developer Experience Pulse"
frequency: "monthly"
questions:
  - id: dx_001
    text: "How easy is it to get your code to production?"
    type: likert  # 1-5
  - id: dx_002
    text: "How often do you feel blocked by CI/CD issues?"
    type: likert  # 1=daily, 5=never
  - id: dx_003
    text: "How confident are you that the build will pass when you push?"
    type: likert
  - id: dx_004
    text: "How long does it take a new team member to make their first production deployment?"
    type: single_select  # >1 month, 2 weeks, 1 week, 1 day, <1 day
  - id: dx_005
    text: "How satisfied are you with your team's CI/CD tooling overall?"
    type: likert
```

**Files to create:**
- `compass/question_bank/dimensions/dx_pulse.yaml` (NEW)
- `ui/pages/dx_survey.py` (NEW — lightweight survey page)
- `callbacks/dx_survey_callbacks.py` (NEW)

#### 3.2 Predictive Analytics (Databricks ML)

**What:** Use historical data to predict CI failures and identify systemic issues.

**Feature 1: Predictive CI Failure**
```python
# analytics/predictive_failure.py
def train_failure_predictor(pipeline_executions: pd.DataFrame) -> dict:
    """
    Features: file_paths_changed, PR_size, author_tenure, time_of_day,
              day_of_week, recent_failure_rate, branch_age
    Target: build_result (success/failure)
    Returns: model artifact + feature importances
    """
```

**Feature 2: Flaky Test Clustering**
```python
# analytics/flaky_tests.py
def detect_flaky_tests(test_executions: pd.DataFrame) -> list[dict]:
    """
    Identifies tests that pass and fail on the same commit SHA.
    Clusters flaky tests by root cause (shared fixtures, timing, DB mocks).
    Returns: [{test_name, flake_rate, cluster_id, likely_cause}]
    """
```

**Feature 3: Anomaly Detection on Scores**
```python
# analytics/anomaly_detection.py
def detect_score_anomalies(maturity_trends: pd.DataFrame) -> list[dict]:
    """
    Detects sudden drops in maturity scores using Z-score or IQR.
    Triggers coaching alerts for teams with unexpected regression.
    """
```

**Files to create:**
- `analytics/__init__.py` (NEW)
- `analytics/predictive_failure.py` (NEW)
- `analytics/flaky_tests.py` (NEW)
- `analytics/anomaly_detection.py` (NEW)

#### 3.3 LLM-Powered Remediation Suggestions

**What:** When a hygiene check fails, use an LLM to generate specific remediation steps based on the team's actual codebase.

```python
# analytics/remediation_engine.py
def generate_remediation(check_result: dict, repo_context: dict) -> str:
    """
    Given a failing hygiene check and repo context,
    generate specific remediation steps.

    Example:
    Input: check="branch_protection_missing", repo={"platform":"github", "repo":"acme/payments"}
    Output: "Enable branch protection on `main`:
             1. Go to Settings → Branches → Branch protection rules
             2. Add rule for `main`
             3. Check 'Require pull request reviews before merging'
             4. Set 'Required number of approvals' to 2
             5. Check 'Require status checks to pass before merging'
             6. Add your CI workflow as a required status check"
    """
```

**Implementation:** Use Databricks Foundation Model APIs (or OpenAI/Anthropic API for standalone) to generate contextual remediation.

**Files to create:**
- `analytics/remediation_engine.py` (NEW)
- `config/llm_config.py` (NEW — API key management)

#### 3.4 Enhanced Exports (PDF/PPTX)

**What:** Update exports to include DORA metrics, hygiene summary, confidence badges, and golden path adoption.

**PDF additions:**
1. DORA Metrics page — 5 metrics with tier badges and trend sparklines
2. Hygiene Check Summary — Per-platform pass/warn/fail counts with top failures listed
3. Confidence badges (High/Medium/Low) next to each dimension score
4. Golden Path adoption % with trend chart
5. Remediation recommendations (top 5 from roadmap engine)

**PPTX additions:**
1. Slide 6: DORA Metrics (4 quadrant layout with tier classification)
2. Slide 7: Hygiene Health (platform-by-platform traffic light grid)
3. Slide 8: Golden Path Adoption (pie + trend)
4. Update overall score slide to include confidence indicator
5. Add executive talking points (auto-generated from insights engine)

**Files to modify:**
- `compass/export_pdf.py` — Add 3 new sections
- `compass/export_pptx.py` — Add 3 new slides (target: 13 slides total)

---

### PHASE 4: Operationalization & Scale (Week 8-10)

> **Goal:** Make the product operational for real organizations.

#### 4.1 Notification & Alerting System

**What:** Automated alerts when scores drop, hygiene checks fail, or non-standard deployments occur.

**Channels:**
- Slack webhook integration
- Microsoft Teams webhook
- Email (SMTP/SendGrid)
- Jira ticket creation (auto-create tech debt tickets)

```python
# notifications/dispatcher.py
class AlertDispatcher:
    """Routes alerts to configured notification channels."""

    def dispatch(self, alert: CoachingAlert) -> None:
        for channel in self._get_channels(alert.team_id):
            if channel.type == "slack":
                self._send_slack(channel, alert)
            elif channel.type == "jira":
                self._create_jira_ticket(channel, alert)
            elif channel.type == "email":
                self._send_email(channel, alert)

# Alert types:
# - score_drop: Team maturity score dropped >10 points week-over-week
# - non_standard_deploy: Non-golden-path deployment detected
# - hard_gate_failure: Critical hygiene check failed (e.g., no branch protection)
# - stale_data: Connector hasn't synced in >24 hours
# - assessment_due: No assessment completed in >90 days
```

**Files to create:**
- `notifications/__init__.py` (NEW)
- `notifications/dispatcher.py` (NEW)
- `notifications/channels/slack.py` (NEW)
- `notifications/channels/teams.py` (NEW)
- `notifications/channels/email.py` (NEW)
- `notifications/channels/jira.py` (NEW)
- `ui/pages/notification_settings.py` (NEW — admin page for channel config)

#### 4.2 Gamification & Team Engagement

**What:** Leaderboards, badges, and success celebrations to drive voluntary adoption (per Spotify Soundcheck model).

**Features:**
1. **Team leaderboard** — Ranked by composite score with tier badges
2. **Achievement badges:**
   - "Golden Path Champion" — 90%+ golden path adoption for 4 consecutive weeks
   - "Security First" — All security hygiene checks passing
   - "Speed Demon" — Build times under 5 minutes
   - "Test Master" — >80% test coverage
   - "Consistency King" — Score improved 3 consecutive periods
3. **Improvement streak tracker** — "Team Alpha has improved for 6 consecutive weeks"
4. **Success stories** — Automatically highlight teams that moved up a tier

```python
# gamification/badges.py
BADGE_DEFINITIONS = [
    {
        "id": "golden_path_champion",
        "name": "Golden Path Champion",
        "icon": "fas fa-road",
        "color": "#22C55E",
        "criteria": "golden_path_adoption >= 90% for 4 consecutive weeks",
        "check": lambda scores: all(s.golden_path >= 90 for s in scores[-4:]),
    },
    # ... more badges
]
```

**Files to create:**
- `gamification/__init__.py` (NEW)
- `gamification/badges.py` (NEW)
- `gamification/leaderboard.py` (NEW)
- `ui/components/badge_display.py` (NEW)
- `ui/components/achievement_toast.py` (NEW)

#### 4.3 ROI Calculator

**What:** Quantify the business value of CI/CD maturity improvements (per McKinsey DVI and Databricks App Spec).

**Calculations:**
```python
# analytics/roi_calculator.py

def compute_roi(before_scores: dict, after_scores: dict, org_context: dict) -> dict:
    """
    Inputs:
    - before/after maturity scores
    - org_context: engineer_count, avg_salary, deploy_frequency, incident_rate

    Outputs:
    - developer_hours_saved: from faster builds and fewer incidents
    - incident_cost_reduction: from improved MTTR and lower CFR
    - deployment_velocity_gain: from increased deploy frequency
    - compliance_risk_reduction: from hygiene check improvements
    - total_annual_value: sum of all savings
    """
```

**Industry benchmarks to use:**
- Elite performers deploy 182x more frequently (DORA 2024)
- 75-90% reduction in remediation work from automation (Forrester)
- Top DVI quartile: 4-5x revenue growth (McKinsey)
- Prioritized tech debt: 2-3% of code but 11-16% of commits (CodeScene)

**Files to create:**
- `analytics/roi_calculator.py` (NEW)
- `ui/pages/roi_dashboard.py` (NEW)
- `callbacks/roi_callbacks.py` (NEW)

#### 4.4 FastAPI REST API

**What:** Headless API for CLI tools, CI/CD integration, and third-party dashboards.

```python
# api/main.py
from fastapi import FastAPI, Depends
from api.auth import get_current_user

app = FastAPI(title="Pipeline Compass API", version="3.0")

@app.get("/api/v1/assessments")
async def list_assessments(user=Depends(get_current_user)):
    ...

@app.post("/api/v1/assessments/{id}/score")
async def trigger_scoring(id: str, user=Depends(get_current_user)):
    ...

@app.get("/api/v1/hygiene/{platform}")
async def get_hygiene_scores(platform: str, user=Depends(get_current_user)):
    ...

@app.get("/api/v1/dora")
async def get_dora_metrics(team_id: str = None, user=Depends(get_current_user)):
    ...

@app.post("/api/v1/connectors/sync")
async def trigger_sync(connector_id: str, user=Depends(get_current_user)):
    ...

@app.get("/api/v1/golden-path/adoption")
async def get_adoption_metrics(user=Depends(get_current_user)):
    ...

@app.get("/api/v1/export/{format}")
async def export_report(format: str, assessment_id: str, user=Depends(get_current_user)):
    ...
```

**Files to create:**
- `api/__init__.py` (NEW)
- `api/main.py` (NEW)
- `api/auth.py` (NEW)
- `api/routes/assessments.py` (NEW)
- `api/routes/scoring.py` (NEW)
- `api/routes/connectors.py` (NEW)
- `api/routes/hygiene.py` (NEW)
- `api/routes/dora.py` (NEW)
- `api/routes/export.py` (NEW)
- `api/routes/golden_path.py` (NEW)

---

### PHASE 5: Polish & Production Launch (Week 10-12)

> **Goal:** Production-grade quality, comprehensive testing, documentation.

#### 5.1 Comprehensive Test Suite

**Current:** 52 tests covering core logic.
**Target:** 150+ tests covering all critical paths.

**New test files needed:**
```
tests/
├── unit/
│   ├── test_golden_path_classifier.py     # Classification logic
│   ├── test_sync_pipeline.py              # Sync orchestration
│   ├── test_roi_calculator.py             # ROI computations
│   ├── test_badge_engine.py               # Gamification badges
│   ├── test_alert_dispatcher.py           # Notification routing
│   ├── test_remediation_engine.py         # LLM remediation
│   └── test_storage_backends.py           # JSON/Postgres/Databricks
├── integration/
│   ├── test_github_live.py                # Real GitHub API
│   ├── test_gitlab_live.py                # Real GitLab API
│   ├── test_jenkins_live.py               # Real Jenkins API
│   ├── test_ado_live.py                   # Real ADO API
│   ├── test_jira_live.py                  # Real Jira API
│   ├── test_databricks_live.py            # Real Databricks API
│   └── test_end_to_end.py                 # Full pipeline: connect → sync → score → display
└── e2e/
    ├── test_assessment_flow.py            # Full wizard: create → answer → score → export
    └── test_golden_path_flow.py           # Tag → classify → dashboard → alert
```

#### 5.2 Performance Optimization

**What:** Ensure dashboards load in <2 seconds even with 90 days of data across 50+ teams.

- **Caching:** Add `functools.lru_cache` or Redis cache for expensive queries
- **Pagination:** All data tables support server-side pagination
- **Lazy loading:** Charts render progressively, not all at once
- **Query optimization:** Add indexes to Delta tables, optimize SQL JOINs

#### 5.3 Error Handling & Observability

**What:** Production-grade error handling and logging.

```python
# observability/logging.py
import structlog

logger = structlog.get_logger()

# Standard log format:
# {"timestamp": "...", "level": "info", "event": "connector_sync_complete",
#  "platform": "github", "records": 847, "duration_ms": 12345, "team_id": "team_001"}
```

- Add structured logging throughout (replace `print()` calls)
- Add Sentry/Datadog error tracking integration
- Add health check endpoint (`/health`) for monitoring
- Add metrics endpoint (`/metrics`) for Prometheus scraping

#### 5.4 Documentation

**Files to create:**
- `docs/DEPLOYMENT.md` — Step-by-step deployment guide for all 3 modes
- `docs/CONNECTORS.md` — How to configure each CI/CD platform connector
- `docs/SCORING.md` — How the scoring algorithm works (for customer transparency)
- `docs/GOLDEN_PATH.md` — How to set up golden path tracking
- `docs/API.md` — REST API reference (auto-generated from FastAPI OpenAPI spec)

---

## PART 4: EXECUTION PRIORITY MATRIX

| Phase | Duration | Effort | Business Value | Risk |
|-------|----------|--------|----------------|------|
| **Phase 0: Foundation** | 2 weeks | High | Medium (enabling) | LOW — hardening existing code |
| **Phase 1: Golden Path** | 2 weeks | Medium | **CRITICAL** — customer's #1 request | MEDIUM — requires real audit log access |
| **Phase 2: Live Data** | 2 weeks | High | **CRITICAL** — differentiator vs questionnaire | HIGH — first real API integration |
| **Phase 3: Intelligence** | 2 weeks | Medium | HIGH — competitive differentiation | MEDIUM — ML/LLM integration |
| **Phase 4: Operations** | 2 weeks | Medium | HIGH — multi-customer scale | LOW — well-understood patterns |
| **Phase 5: Polish** | 2 weeks | Medium | MEDIUM — production readiness | LOW — testing and docs |

**Total: 12 weeks (3 months) to v3 production launch**

---

## PART 5: KEY METRICS FOR SUCCESS

### Launch Criteria (must have before v3 release)

- [ ] At least ONE connector (GitHub or ADO) validated against real API with real credentials
- [ ] Golden path classification running against real Databricks audit logs
- [ ] Hygiene scores computed from live telemetry (not just mock data)
- [ ] DORA metrics computed from live CI/CD pipeline data
- [ ] Authentication works in at least ONE mode (Databricks or OAuth)
- [ ] Docker deployment works end-to-end
- [ ] 100+ tests passing (up from 52)
- [ ] PDF/PPTX exports include DORA + hygiene sections
- [ ] Golden path adoption dashboard renders with real data

### Success Metrics (measure after launch)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Assessment completion rate** | >80% started assessments completed | `completed / started` |
| **Connector adoption** | >2 platforms connected per org | Count per org |
| **Golden path adoption** | Visible improvement over 90 days | Trend chart |
| **Score accuracy** | <15 point gap between telemetry and assessment | Discrepancy analysis |
| **Dashboard load time** | <2 seconds | Performance monitoring |
| **Export quality** | Customer accepts PDF as client deliverable | Customer feedback |

---

## PART 6: ANTI-PATTERNS TO AVOID IN v3

These patterns plagued v1/v2. Do NOT repeat them.

### 1. "Code Complete" != "Working"
Every connector, query, and scorer MUST be validated against real systems before being marked done. A function that has never executed against a real API is NOT complete — it's a hypothesis.

### 2. Mock Data as the Only Path
Mock data is for development and testing. The production path (real APIs → real scoring → real dashboards) must be the PRIMARY development focus. Build mock AFTER real works, not before.

### 3. Breadth Over Depth
Don't build 6 connectors at 60% quality. Build 1 connector at 100% quality, then replicate the pattern. Start with GitHub (most common), validate end-to-end, THEN expand to ADO, Jenkins, etc.

### 4. UI Before Data
Don't build dashboard pages that display mock data and call it "done." Build the data pipeline first, verify scores are correct, THEN build the UI to display them. The UI is the LAST step, not the first.

### 5. "Scaffold and Verify Later"
Every function must be exercised by a test or manual verification before PR merge. The `****Checked and Verified as Real*****` annotations are a start, but they annotated code that was only verified against mock data. v3 verification means: "this code ran against a real GitHub/GitLab/Databricks API and produced correct results."

---

## PART 7: FILE MANIFEST — ALL NEW FILES FOR v3

```
NEW FILES (57 files):
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   └── routes/
│       ├── assessments.py
│       ├── scoring.py
│       ├── connectors.py
│       ├── hygiene.py
│       ├── dora.py
│       ├── export.py
│       └── golden_path.py
├── auth/
│   ├── __init__.py
│   ├── databricks_auth.py
│   ├── oauth.py
│   ├── dev_auth.py
│   └── middleware.py
├── analytics/
│   ├── __init__.py
│   ├── predictive_failure.py
│   ├── flaky_tests.py
│   ├── anomaly_detection.py
│   ├── remediation_engine.py
│   └── roi_calculator.py
├── gamification/
│   ├── __init__.py
│   ├── badges.py
│   └── leaderboard.py
├── notifications/
│   ├── __init__.py
│   ├── dispatcher.py
│   └── channels/
│       ├── slack.py
│       ├── teams.py
│       ├── email.py
│       └── jira.py
├── ingestion/
│   ├── golden_path_classifier.py
│   ├── sync_pipeline.py
│   └── sync_state.py
├── templates/
│   ├── github_golden_path.yml
│   ├── ado_golden_path.yml
│   ├── gitlab_golden_path.yml
│   ├── jenkins_golden_path.groovy
│   └── databricks_golden_path.py
├── ui/
│   ├── pages/
│   │   ├── golden_path_adoption.py
│   │   ├── dx_survey.py
│   │   ├── roi_dashboard.py
│   │   └── notification_settings.py
│   └── components/
│       ├── adoption_pie.py
│       ├── team_heatmap.py
│       ├── leaderboard.py
│       ├── badge_display.py
│       └── achievement_toast.py
├── callbacks/
│   ├── golden_path_callbacks.py
│   ├── dx_survey_callbacks.py
│   └── roi_callbacks.py
├── tests/
│   ├── unit/
│   │   ├── test_golden_path_classifier.py
│   │   ├── test_sync_pipeline.py
│   │   ├── test_roi_calculator.py
│   │   ├── test_badge_engine.py
│   │   └── test_storage_backends.py
│   ├── integration/
│   │   ├── conftest.py
│   │   ├── test_github_live.py
│   │   ├── test_gitlab_live.py
│   │   ├── test_jenkins_live.py
│   │   ├── test_ado_live.py
│   │   ├── test_jira_live.py
│   │   ├── test_databricks_live.py
│   │   └── test_end_to_end.py
│   └── e2e/
│       ├── test_assessment_flow.py
│       └── test_golden_path_flow.py
├── docs/
│   ├── DEPLOYMENT.md
│   ├── CONNECTORS.md
│   ├── SCORING.md
│   ├── GOLDEN_PATH.md
│   └── API.md
├── Dockerfile
├── Dockerfile.api
├── docker-compose.yml
├── .dockerignore
├── .github/workflows/ci.yml
└── config/llm_config.py

MODIFIED FILES (25+ files):
├── app.py                          — Auth integration, health endpoint
├── data_layer/queries/raw_ddl.py   — Expand to 33 tables
├── data_layer/queries/normalized_ddl.py — Add repo_hygiene, test_executions
├── compass/export_pdf.py           — DORA, hygiene, confidence sections
├── compass/export_pptx.py          — 3 new slides
├── ui/sidebar.py                   — New nav items
├── callbacks/navigation_callbacks.py — New page routes
├── ui/pages/data_sources.py        — Redesign to management console
├── callbacks/datasource_callbacks.py — Sync triggers, health checks
├── notebooks/05-08                 — Wire to real pipeline
├── All 6 connectors                — Add retry, health_check, error handling
├── requirements.txt                — Pin versions, add new deps
└── config/settings.py              — Auth, notification, LLM config
```

---

## APPENDIX A: Document Cross-Reference

| Source Document | Key Contributions to v3 Plan |
|----------------|------------------------------|
| **Golden Path PDF** | Phase 1 entirely (tagging, classification, adoption dashboard, Jira correlation) |
| **Databricks App Spec** | Lakehouse architecture, DORA metrics catalog, AI/predictive features, persona-based dashboards |
| **cicd_maturity_app_plan.md** | System table queries, custom table DDL, scoring domain weights, nightly aggregation |
| **Industry Research (compass_artifact)** | SPACE framework, gamification (Spotify), scoreboard platforms (Cortex/OpsLevel), DORA benchmarks, anti-gaming guidance |
| **CI/CD & Data Hygiene Metrics** | Hygiene scoring matrix depth, visualization patterns, operationalization strategies |
| **PIPELINE_COMPASS_BUILD_PLAN** | Original architecture (React/FastAPI), question bank format, directory structure, deployment target |
| **IMPROVEMENT_PLAN_V2** | Bug fixes (all done), connector architecture, hybrid scoring spec, Phase 1-6 roadmap |
| **FIX_PLAN** | 16 specific tasks (most done), acceptance criteria patterns |

## APPENDIX B: Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Real API integration reveals schema mismatches | HIGH | HIGH | Phase 0 integration tests; start with 1 platform, not 6 |
| Databricks system tables unavailable in customer workspace | HIGH | MEDIUM | Graceful fallback; score from assessment-only when no telemetry |
| LLM remediation generates incorrect guidance | MEDIUM | MEDIUM | Human review step; "AI-generated" badge; feedback loop |
| Rate limiting crashes during large sync | HIGH | MEDIUM | Exponential backoff; batch size limits; progress tracking |
| Customer rejects Dash UI, wants React | HIGH | LOW | FastAPI layer enables future React frontend without backend rewrite |
| Auth integration blocks deployment | HIGH | MEDIUM | Dev mode (no auth) always available; auth is additive, not blocking |
| Golden path token circumvented by teams | MEDIUM | MEDIUM | Multiple classification signals (SP detection, IP matching, git source) — not just token |
