# CI/CD Maturity Intelligence App

A comprehensive CI/CD maturity assessment and observability platform built on Databricks, designed to measure, score, and improve engineering team practices across deployment automation, pipeline reliability, security governance, and data quality.

## Live URL

**Production:** [blueprint-cicd-maturity](https://blueprint-cicd-maturity-1866518241053589.9.azure.databricksapps.com)

Deployed as a Databricks App on Azure Databricks workspace `adb-1866518241053589.9.azuredatabricks.net`.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Databricks App (Gunicorn)                    │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │  Dash UI  │  │  Callbacks   │  │  Compass Scoring Engine   │  │
│  │ 17 Pages  │  │  (reactive)  │  │  Assessment + Telemetry   │  │
│  └─────┬─────┘  └──────┬───────┘  └────────────┬──────────────┘  │
│        │               │                        │                │
│  ┌─────▼───────────────▼────────────────────────▼──────────────┐ │
│  │                   Data Layer                                 │ │
│  │  custom_tables.py → system_tables.py → Databricks SQL        │ │
│  │                  ↘ precomputed/*.json (fallback)              │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐         ┌───────────────────────┐
│ System Tables   │         │  Custom Delta Tables   │
│ (Unity Catalog) │         │  (demos.cicd.*)        │
├─────────────────┤         ├───────────────────────┤
│ access.audit    │         │ team_registry          │
│ lakeflow.jobs   │         │ maturity_scores        │
│ lakeflow.runs   │         │ maturity_trends        │
│ compute.clusters│         │ staged_dora_metrics    │
│ billing.usage   │         │ external_quality_metrics│
│ info_schema     │         │ coaching_alerts        │
└─────────────────┘         └───────────────────────┘
```

## Key Features

### Compass Assessment Engine
- **50+ question assessment** across 9 maturity domains
- **Anti-pattern detection** (manual gates, hero deployers, etc.)
- **Archetype classification** (Startup, Scaling, Enterprise, etc.)
- **Roadmap generation** with prioritized improvement actions
- **PDF/PPTX export** for executive presentations

### DORA Metrics (Real Data)
- **Deployment Frequency** — derived from `system.access.audit` job/pipeline runs
- **Change Failure Rate** — ratio of failed to total deployments
- **Recovery Time (MTTR)** — time between failure and next success
- **Lead Time for Changes** — (requires GitHub PR connector, in progress)
- **Rework Rate** — repeated failures on same components

### Platform Telemetry (9 Scoring Domains)
| Domain | Source | What It Measures |
|--------|--------|-----------------|
| Pipeline Reliability | `system.lakeflow.job_run_timeline` | Job success rate (99.7% current) |
| Golden Path Adoption | `system.access.audit` | % deployments via service principals |
| Cluster Security | `system.compute.clusters` | Policy coverage (58.4% current) |
| Git-Backed Pipelines | `system.lakeflow.jobs` | DABs/git-source adoption |
| Environment Promotion | `system.access.audit` | Dev → staging → prod flow |
| Data Quality | `system.information_schema` + DLT events | Constraints + expectations |
| Cost Efficiency | `system.billing.usage` | DBU consumption patterns |
| Deployment Frequency | `system.access.audit` | DORA deployment frequency |
| Security & Governance | Cluster policies + UC adoption | Governance posture |

### Hygiene Dashboard
- Real-time platform health checks
- Cluster configuration hygiene
- Unity Catalog adoption tracking
- DLT pipeline quality monitoring

## Pages

| # | Page | Description |
|---|------|-------------|
| 1 | **Executive Summary** | 3-state landing: welcome → assessment → full telemetry |
| 2 | **Compass Assessment** | Interactive 50+ question maturity survey |
| 3 | **Compass Results** | Spider chart, dimension scores, anti-patterns |
| 4 | **Compass Roadmap** | Prioritized improvement actions with effort/impact |
| 5 | **Compass History** | Assessment history and trend tracking |
| 6 | **DORA Metrics** | 5 DORA KPIs with tier classification and trends |
| 7 | **Trend Analysis** | Maturity score trends over time (weekly/monthly) |
| 8 | **Team Drilldown** | Per-team deep dive with dimension breakdown |
| 9 | **Golden Path Adoption** | Service principal vs human deployment tracking |
| 10 | **Deployment Explorer** | Deployment event browser with filters |
| 11 | **Correlation Analysis** | Cross-metric correlation heatmaps |
| 12 | **Hygiene Dashboard** | Platform health checks and compliance |
| 13 | **Databricks Deep Dive** | DABs, packaging, UC, cluster, DLT analysis |
| 14 | **Data Sources** | Connector status (GitHub, Jira, ADO) |
| 15 | **Scoring Logic** | Transparent view of scoring methodology |
| 16 | **ROI Dashboard** | Cost savings and efficiency gains |
| 17 | **Admin** | Configuration and data source management |

## Data Flow

The app uses a **three-tier data strategy** with automatic fallback:

1. **Live SQL** — Queries Databricks system tables and custom Delta tables via SQL warehouse
2. **Precomputed JSON** — Falls back to pre-exported JSON files when the warehouse is unavailable
3. **Mock Data** — CSV-based mock data for local development (`USE_MOCK=true`)

```
Request → custom_tables.py
             ├─ is_mock? → MockDataProvider (CSV)
             └─ live mode:
                  ├─ Try SQL query → system_tables.py → Databricks SQL Warehouse
                  └─ On failure → precomputed/*.json (always available)
```

### Precomputed Data Files
Located in `data_layer/precomputed/`:

| File | Records | Source |
|------|---------|--------|
| `team_registry.json` | 1 | `demos.cicd.team_registry` |
| `maturity_scores.json` | 81 | Computed from system tables (9 domains × 9 weeks) |
| `maturity_trends.json` | 11 | Weekly + monthly rollups |
| `staged_dora_metrics.json` | 5 | Computed from `system.access.audit` |
| `deployment_events.json` | 10,000 | From `system.access.audit` |
| `pipeline_runs.json` | 500 | From `system.lakeflow.job_run_timeline` |
| `clusters.json` | 200 | From `system.compute.clusters` |
| `jobs.json` | 200 | From `system.lakeflow.jobs` |
| `external_quality_metrics.json` | 63 | GitHub commit data |

## Project Structure

```
CICDApp/
├── app.py                    # Dash app entry point
├── app.yaml                  # Databricks Apps deployment config
├── requirements.txt          # Python dependencies
├── callbacks/                # Dash callback modules
│   ├── dora_callbacks.py
│   ├── executive_callbacks.py
│   └── ...
├── compass/                  # Scoring & assessment engine
│   ├── scoring_engine.py     # 9-domain maturity scoring
│   ├── scoring_constants.py  # Tier thresholds, DORA benchmarks
│   ├── dora_calculator.py    # DORA metrics computation
│   ├── assessment_store.py   # Assessment persistence
│   ├── hygiene_scorer.py     # Platform health checks
│   ├── antipattern_engine.py # Anti-pattern detection
│   ├── archetype_engine.py   # Team archetype classification
│   ├── roadmap_engine.py     # Improvement roadmap generation
│   ├── export_pdf.py         # PDF report generation
│   ├── export_pptx.py        # PowerPoint export
│   └── question_bank/        # Assessment questions by domain
├── config/
│   ├── settings.py           # App configuration (env vars, catalog, schema)
│   └── data_source_configs.json
├── data_layer/
│   ├── connection.py         # Singleton DataConnection (mock/live routing)
│   ├── queries/
│   │   ├── custom_tables.py  # Main query router with fallback logic
│   │   └── system_tables.py  # Databricks system table queries
│   ├── precomputed/          # JSON fallback data (warehouse-independent)
│   │   ├── __init__.py       # Loader functions
│   │   └── *.json            # Pre-exported data files
│   └── mock/
│       └── mock_provider.py  # CSV-based mock data for local dev
├── ui/
│   ├── theme.py              # Dark theme tokens, tier colors
│   ├── components/           # Reusable UI components
│   │   ├── kpi_card.py
│   │   ├── tier_badge.py
│   │   ├── dora_tiles.py
│   │   └── ...
│   └── pages/                # 17 page layouts
│       ├── executive_summary.py
│       ├── dora_metrics.py
│       ├── databricks_deep_dive.py
│       └── ...
├── assets/                   # CSS, fonts, images
├── tests/                    # Test suite
└── notebooks/                # Databricks notebooks for data export
```

## Setup

### Prerequisites
- Python 3.11+
- Databricks workspace with Unity Catalog enabled
- System tables access granted to the app service principal

### Local Development

```bash
# Clone and install
git clone <repo-url>
cd CICDApp
pip install -r requirements.txt

# Run in mock mode (no Databricks connection needed)
export CICD_APP_USE_MOCK=true
python app.py
```

### Databricks Deployment

```bash
# Configure Databricks CLI
databricks auth profiles

# Sync code to workspace
databricks sync . /Workspace/Users/<you>/cicd-maturity-app --profile <profile>

# Deploy the app
databricks apps deploy blueprint-cicd-maturity \
  --source-code-path /Workspace/Users/<you>/cicd-maturity-app \
  --profile <profile>
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CICD_APP_USE_MOCK` | `false` | Enable mock data mode for local dev |
| `AUTH_MODE` | `dev` | `databricks` for Apps auth, `dev` for token-based |
| `CICD_APP_CATALOG` | `demos` | Unity Catalog name |
| `CICD_APP_SCHEMA` | `cicd` | Schema for custom tables |
| `DATABRICKS_WAREHOUSE_HTTP_PATH` | — | SQL warehouse HTTP path |
| `DATABRICKS_SERVER_HOSTNAME` | — | Workspace hostname (external mode) |
| `DATABRICKS_TOKEN` | — | PAT token (external mode only) |

## System Table Permissions

The app service principal needs `SELECT` access to:

```sql
GRANT USE CATALOG ON CATALOG system TO `app-service-principal`;
GRANT USE SCHEMA ON SCHEMA system.access TO `app-service-principal`;
GRANT SELECT ON TABLE system.access.audit TO `app-service-principal`;
GRANT SELECT ON TABLE system.lakeflow.job_run_timeline TO `app-service-principal`;
GRANT SELECT ON TABLE system.lakeflow.jobs TO `app-service-principal`;
GRANT SELECT ON TABLE system.compute.clusters TO `app-service-principal`;
GRANT SELECT ON TABLE system.billing.usage TO `app-service-principal`;
GRANT SELECT ON TABLE system.information_schema.table_constraints TO `app-service-principal`;
```

## Current Maturity Scores (Real Data)

As of April 2026, computed from workspace telemetry:

| Metric | Value | Tier |
|--------|-------|------|
| **Composite Score** | 56.3 | Defined |
| Pipeline Reliability | 99.7% success rate | Elite |
| Deployment Frequency | 0.58/day | High |
| Change Failure Rate | 1.96% | Elite |
| Cluster Security | 58.4% policy coverage | Developing |
| Golden Path | 0% (all human users) | Initial |

## Tech Stack

- **Frontend:** Dash + Plotly (dark theme)
- **Backend:** Python, Gunicorn
- **Data:** Databricks SQL, Unity Catalog system tables, Delta Lake
- **Deployment:** Databricks Apps (Azure)
- **Auth:** Databricks SDK service principal auth
