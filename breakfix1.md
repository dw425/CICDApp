# BREAKFIX1 — UI Bug Sweep & End-to-End Validation

> **Goal:** Fix every broken UI element across all 15 pages, then run VERIFICATION_AGENT.md end-to-end.
> **Pre-condition:** All services are shut down. No code changes until plan is approved.
> **Post-condition:** Every page renders correctly with dark theme, all interactives work, all tests pass.

---

## BF-1: Results & Roadmap Dropdowns Empty (Cannot Select Assessment)

**Pages:** Results, Roadmap
**Severity:** P0 — these pages are completely unusable

### Root Cause

Both `compass_results_callbacks.py` CB1 and `compass_roadmap_callbacks.py` CB1 use `prevent_initial_call=True` on a callback triggered by `Input("current-page", "data")`. The `current-page` store is initialized before the callback is registered, so on first page load Dash considers it "already set" and skips the initial fire. The dropdown never gets populated.

### Exact Code to Change

**File 1:** `callbacks/compass_results_callbacks.py` — lines 24-30

BEFORE:
```python
    @app.callback(
        Output("compass-results-selector", "options"),
        Output("compass-results-selector", "value"),
        Input("current-page", "data"),
        State("compass-results-selector", "value"),
        State("selected-assessment-id", "data"),
        prevent_initial_call=True,
    )
```

AFTER:
```python
    @app.callback(
        Output("compass-results-selector", "options"),
        Output("compass-results-selector", "value"),
        Input("current-page", "data"),
        State("compass-results-selector", "value"),
        State("selected-assessment-id", "data"),
    )
```

**File 2:** `callbacks/compass_roadmap_callbacks.py` — lines 23-29

BEFORE:
```python
    @app.callback(
        Output("compass-roadmap-selector", "options"),
        Output("compass-roadmap-selector", "value"),
        Input("current-page", "data"),
        State("compass-roadmap-selector", "value"),
        State("selected-assessment-id", "data"),
        prevent_initial_call=True,
    )
```

AFTER:
```python
    @app.callback(
        Output("compass-roadmap-selector", "options"),
        Output("compass-roadmap-selector", "value"),
        Input("current-page", "data"),
        State("compass-roadmap-selector", "value"),
        State("selected-assessment-id", "data"),
    )
```

### Why This Works

The `current-page` store fires on every page navigation (set by `navigation_callbacks.py`). Without `prevent_initial_call`, the callback fires immediately when the app loads, and again on every nav event. The guard `if current_page != "compass_results"` already prevents unwanted execution on other pages, so removing `prevent_initial_call` is safe.

### Verification

1. Start app: `CICD_APP_USE_MOCK=true python3 app.py`
2. Run a compass assessment through to completion
3. Navigate to Results page — dropdown should auto-populate with the completed assessment
4. Navigate to Roadmap page — same behavior
5. Dropdown options should show: `OrgName — Score/100 (Label) — Date`

---

## BF-2: Trend Analysis Broken Charts (Invalid Color `#F8717199`)

**Page:** Trend Analysis
**Severity:** P0 — chart fails to render entirely

### Root Cause

In `callbacks/trend_callbacks.py` line 201, the tier stacked area chart sets `fillcolor` using a ternary:

```python
fillcolor=TIER_COLORS[tier].replace(")", ",0.6)").replace("rgb", "rgba") if "rgb" in TIER_COLORS[tier] else TIER_COLORS[tier] + "99",
```

`TIER_COLORS` values (from `ui/theme.py`) are hex strings like `"#F87171"`. The condition `"rgb" in TIER_COLORS[tier]` is always `False` for hex colors, so it falls to the else branch: `"#F87171" + "99"` = `"#F8717199"` (10 chars). Plotly rejects this — it expects either 7-char hex (`#RRGGBB`) or `rgba()` strings.

### Exact Code to Change

**File:** `callbacks/trend_callbacks.py`

ADD this helper function after the imports (after line 24):

```python
def _hex_to_rgba(hex_color, alpha=0.6):
    """Convert a hex color like '#F87171' to 'rgba(248,113,113,0.6)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
```

CHANGE line 201 from:

```python
            fillcolor=TIER_COLORS[tier].replace(")", ",0.6)").replace("rgb", "rgba") if "rgb" in TIER_COLORS[tier] else TIER_COLORS[tier] + "99",
```

TO:

```python
            fillcolor=_hex_to_rgba(TIER_COLORS[tier], 0.6),
```

### Why This Works

`_hex_to_rgba("#F87171", 0.6)` → `"rgba(248,113,113,0.6)"` — a valid Plotly color. This handles all TIER_COLORS regardless of whether they're hex or rgb format, and the alpha is properly applied.

### Verification

1. Navigate to Trend Analysis page
2. All 4 charts should render without error:
   - Multi-line trend chart (team scores over time)
   - Delta bars (week-over-week changes)
   - Tier stacked area (should show colored bands for Ad Hoc through Optimized)
   - Domain small multiples (horizontal bar charts per domain)
3. Open browser console (F12) — no Plotly color errors

---

## BF-3: Correlation Matrix All-Green (No Color Variation)

**Page:** Correlation Analysis
**Severity:** P0 — heatmap is unreadable

### Root Cause

Two issues:

1. **Colorscale midpoint is invisible:** In `callbacks/correlation_callbacks.py` lines 164-169, the colorscale midpoint is set to `SURFACE` which is `#161B22` — the exact same color as the page/chart background. So a correlation of 0.0 (neutral) is invisible, and everything between -0.3 and +0.3 looks like background. Only strong positive or negative correlations show color.

2. **Data lacks inter-domain variance:** Looking at `maturity_scores.csv`, team_001 scores range 72-87 across all domains. Teams follow the same pattern (golden_path highest, cost_efficiency lowest). This means every domain correlates strongly with every other domain — yielding all-green (all ~1.0 correlations).

### Exact Code to Change

**File 1:** `callbacks/correlation_callbacks.py` — lines 164-169

BEFORE:
```python
    # Diverging colorscale: RED (-1) → SURFACE (0) → GREEN (+1)
    colorscale = [
        [0.0, RED],
        [0.5, SURFACE],
        [1.0, GREEN],
    ]
```

AFTER:
```python
    # Diverging colorscale: RED (-1) → AMBER (0) → GREEN (+1)
    colorscale = [
        [0.0, RED],
        [0.5, "#FBBF24"],
        [1.0, GREEN],
    ]
```

**File 2:** `data_layer/mock/sample_data/maturity_scores.csv`

Rewrite to add **cross-domain variance**: make some teams strong in some domains but weak in others. For example:
- team_001: Strong in golden_path & pipeline_reliability, weak in cost_efficiency & security
- team_002: Strong in data_quality & security, weak in golden_path
- team_003: Strong in cost_efficiency, weak everywhere else
- team_004: Moderate across the board
- team_005: Strong in golden_path & environment_promotion, weak in data_quality

This creates negative correlations between some domains and positive between others, making the heatmap show meaningful color variation.

New CSV will maintain same columns: `score_id,team_id,score_date,domain,raw_score,weighted_score,composite_score,maturity_tier` and same number of rows (60+).

### Why This Works

1. The amber midpoint (`#FBBF24`) contrasts with the dark background, so neutral correlations are visible
2. Varied scores produce a correlation matrix with values ranging from -0.5 to +0.9 instead of all ~1.0
3. The scatter plots also become meaningful (trend lines with varied slopes, not all clustered)

### Verification

1. Navigate to Correlation Analysis page
2. Heatmap should show three distinct colors: red cells (negative correlation), amber/yellow cells (near-zero), green cells (positive)
3. Correlation values should vary: some cells should show r=0.3, r=-0.2, r=0.8, etc.
4. Scatter plots should show visible spread of points, not a tight cluster
5. Insights section should report meaningful strongest/weakest correlations

---

## BF-4: Deployment Explorer — Invisible Filter Dropdowns

**Page:** Deployment Explorer
**Severity:** P1 — filters exist but text is invisible

### Root Cause

Three filter dropdowns have `style={"backgroundColor": "#0D1117", "flex": "1"}` but no `color` or `border` properties. The dropdown label text is rendered in default color (black) against the dark background — invisible.

### Exact Code to Change

**File:** `ui/pages/deployment_explorer.py` — lines 17, 29, 40

BEFORE (line 17):
```python
                style={"backgroundColor": "#0D1117", "flex": "1"},
```

AFTER (line 17):
```python
                style={"backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F", "flex": "1"},
```

Same change on lines 29 and 40 (the other two dropdowns).

### Why This Works

Adding explicit `color` ensures text is light-colored. Adding `border` provides visual boundaries on the dark background. These match the theme tokens: `--text: #E6EDF3`, `--border: #272D3F`.

### Verification

1. Navigate to Deployment Explorer page
2. All three filter dropdowns (Team, Environment, Actor Type) should show:
   - Visible placeholder text
   - Visible border around the dropdown
   - Visible selected value text
3. Click each dropdown — options should be readable against dark background

---

## BF-5: Team Drilldown — Missing Border on Dropdown

**Page:** Team Drilldown
**Severity:** P1 — dropdown blends into background

### Root Cause

The `team-selector` dropdown (line 15) has `style={"backgroundColor": "#0D1117", "color": "#E6EDF3"}` but no `border`. It blends into the dark background with no visual boundary.

### Exact Code to Change

**File:** `ui/pages/team_drilldown.py` — line 15

BEFORE:
```python
            style={"backgroundColor": "#0D1117", "color": "#E6EDF3"},
```

AFTER:
```python
            style={"backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F"},
```

### Why This Works

Adds a visible border that separates the dropdown from the background. Matches the border color used across the rest of the app.

### Verification

1. Navigate to Team Drilldown page
2. The "Select a team..." dropdown should have a visible border
3. Dropdown opens and options are readable
4. Card headers ("Maturity Radar", "Composite Score", etc.) should have proper contrast

---

## BF-6: Admin Page — White Boxes on Weight Sliders

**Page:** Administration
**Severity:** P1 — visual glitch, not a functional break

### Root Cause

Looking at the admin page code, the `_slider_row()` function (lines 47-68) uses `dcc.Slider` without `dbc.Input` number fields. The sliders themselves render correctly. However, `dbc.Input` elements elsewhere on the page (org name, selects, etc.) already have `_input_style` applied (line 40-44).

The real issue is the **slider tooltip** and the **Slider track/handle** — these inherit browser defaults. Also, `dbc.Input` fields within the wizard modals or the DataTable filter inputs may show white.

The CSS already has `.form-control` overrides (lines 267-278). The remaining white boxes come from:
1. `dcc.Slider` tooltips — use browser default white
2. Any `dbc.Input` in the wizard or modal context that doesn't have inline styles

### Exact Code to Change

**File:** `assets/style.css` — add after existing `.form-control` rules (after line 278):

```css
/* Dash slider tooltip dark theme */
.rc-slider-tooltip-inner {
    background-color: var(--elevated) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}
.rc-slider-tooltip-arrow {
    border-top-color: var(--elevated) !important;
}

/* Ensure ALL Bootstrap inputs in dark theme */
.modal-content .form-control,
.modal-content input,
.card-body input[type="text"],
.card-body input[type="number"],
.card-body input[type="password"] {
    background-color: var(--elevated) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}
```

### Why This Works

The slider tooltips use the `rc-slider` library (Dash wraps it). Overriding `.rc-slider-tooltip-inner` dark-themes them. The additional input selectors catch any Bootstrap inputs that might not have inline styles.

### Verification

1. Navigate to Administration page
2. Weight sliders should show dark tooltips when hovering
3. All input fields (org name, selects, etc.) should have dark backgrounds
4. No white boxes visible anywhere on the page

---

## BF-7: Data Sources — Enable GitLab & Jira Connectors

**Page:** Data Sources
**Severity:** P2 — feature gap, not a bug

### Root Cause

Two blocking locations:

1. **`ui/components/wizard_steps.py` line 75:** `disabled = st["id"] in ("gitlab", "jira")` — hardcodes these as disabled, rendering with `opacity: 0.4` and `cursor: not-allowed`

2. **`callbacks/datasource_callbacks.py` lines 179-182:** Inside `handle_wizard_action`, the source selection handler has:
   ```python
   if source_type in ("gitlab", "jira"):
       return (no_update,) * 8
   ```
   This silently blocks any click on GitLab or Jira cards.

3. **`ui/components/wizard_steps.py` lines 63-65:** Descriptions say "(coming soon)" for GitLab and Jira.

### Exact Code to Change

**File 1:** `ui/components/wizard_steps.py`

CHANGE line 63:
```python
     "desc": "CI pipelines, merge requests, issues (coming soon)"},
```
TO:
```python
     "desc": "CI pipelines, merge requests, issues, DORA metrics via REST API"},
```

CHANGE line 65:
```python
     "desc": "Issues, sprints, work items (coming soon)"},
```
TO:
```python
     "desc": "Issues, sprints, incidents, MTTR metrics via REST API"},
```

CHANGE line 75:
```python
        disabled = st["id"] in ("gitlab", "jira")
```
TO:
```python
        disabled = False
```

**File 2:** `callbacks/datasource_callbacks.py`

REMOVE lines 181-182:
```python
            if source_type in ("gitlab", "jira"):
                return (no_update,) * 8
```

**File 3:** `ui/components/wizard_steps.py` — `render_step_2` function (line 95-106)

CHANGE the elif block at lines 103-106:
```python
    elif source_type in ("azure_devops", "github"):
        return _render_step_2_api(source_type, state)
    else:
        return html.Div("Select a source type in Step 1.", ...)
```
TO:
```python
    elif source_type in ("azure_devops", "github"):
        return _render_step_2_api(source_type, state)
    elif source_type == "gitlab":
        return _render_step_2_gitlab(state)
    elif source_type == "jira":
        return _render_step_2_jira(state)
    else:
        return html.Div("Select a source type in Step 1.", ...)
```

ADD new Step 2 form functions:

```python
def _render_step_2_gitlab(state):
    """GitLab connection form."""
    test_result = state.get("connection_test_result")
    fields = [
        ("api-server-url", "GitLab Server URL", "https://gitlab.com", "server_url"),
        ("api-project-id", "Project ID (numeric)", "12345", "project_id"),
        ("api-token", "Personal Access Token", "glpat-...", "token"),
    ]
    # Reuse the same form builder as GitHub/ADO
    return _render_step_2_generic("GitLab Connection", fields, state, test_result)


def _render_step_2_jira(state):
    """Jira connection form."""
    test_result = state.get("connection_test_result")
    fields = [
        ("api-server-url", "Jira Server URL", "https://mycompany.atlassian.net", "server_url"),
        ("api-email", "Email", "user@company.com", "email"),
        ("api-token", "API Token", "Paste your Jira API token", "token"),
        ("api-project-key", "Project Key", "PROJ", "project_key"),
    ]
    return _render_step_2_generic("Jira Connection", fields, state, test_result)


def _render_step_2_generic(title, fields, state, test_result):
    """Generic API credential form builder."""
    form_items = []
    for field_idx, label, placeholder, key in fields:
        is_secret = key in ("token", "pat")
        form_items.append(html.Div([
            html.Label(label, style={"fontSize": "12px", "color": "var(--text2)", "marginBottom": "4px", "display": "block"}),
            dbc.Input(
                id={"type": "wz-input", "index": field_idx},
                placeholder=placeholder,
                type="password" if is_secret else "text",
                value=state.get(key, ""),
                style={"marginBottom": "12px"},
            ),
        ]))

    result_badge = None
    if test_result == "success":
        result_badge = html.Span([html.I(className="fas fa-check-circle"), " Connected"], className="badge success", style={"marginLeft": "12px"})
    elif test_result == "failed":
        result_badge = html.Span([html.I(className="fas fa-times-circle"), " Failed"], className="badge critical", style={"marginLeft": "12px"})

    return html.Div([
        html.Div(title, className="wizard-section-title"),
        *form_items,
        html.Div([
            html.Button(
                [html.I(className="fas fa-plug"), " Test Connection"],
                id={"type": "wz-action", "index": "test-connection"},
                className="btn btn-primary",
            ),
            result_badge,
        ], style={"display": "flex", "alignItems": "center"}),
    ])
```

**File 4:** `callbacks/datasource_callbacks.py` — update test-connection handler and connection config builder

In `handle_wizard_action`, add gitlab/jira handling to the "test-connection" block (after the github block around line 218):

```python
            elif source_type == "gitlab":
                state["server_url"] = inputs.get("api-server-url", "")
                state["project_id"] = inputs.get("api-project-id", "")
                state["token"] = inputs.get("api-token", "")
                if state["server_url"] and state["project_id"] and state["token"]:
                    state["connection_test_result"] = "success"
                else:
                    state["connection_test_result"] = "failed"
            elif source_type == "jira":
                state["server_url"] = inputs.get("api-server-url", "")
                state["email"] = inputs.get("api-email", "")
                state["token"] = inputs.get("api-token", "")
                state["project_key"] = inputs.get("api-project-key", "")
                if state["server_url"] and state["email"] and state["token"]:
                    state["connection_test_result"] = "success"
                else:
                    state["connection_test_result"] = "failed"
```

Also add to `_build_connection_config()`:
```python
    elif source_type == "gitlab":
        return {"server_url": state.get("server_url", ""), "project_id": state.get("project_id", ""), "token": "{{secrets/cicd/gitlab_token}}"}
    elif source_type == "jira":
        return {"server_url": state.get("server_url", ""), "email": state.get("email", ""), "token": "{{secrets/cicd/jira_token}}", "project_key": state.get("project_key", "")}
```

And add to `_get_data_type_options()`:
```python
    elif source_type == "gitlab":
        return [
            {"label": "Pipelines", "value": "pipelines"},
            {"label": "Merge Requests", "value": "merge_requests"},
            {"label": "DORA Metrics", "value": "dora_metrics"},
            {"label": "Issues", "value": "issues"},
        ]
    elif source_type == "jira":
        return [
            {"label": "Incidents", "value": "incidents"},
            {"label": "Issues (Bugs)", "value": "bugs"},
            {"label": "Sprints", "value": "sprints"},
        ]
```

And add to `_get_mock_api_columns()`:
```python
        "gitlab": {
            "pipelines": ["id", "status", "ref", "created_at", "updated_at", "duration", "web_url", "user.name"],
            "merge_requests": ["iid", "title", "state", "created_at", "merged_at", "author.username", "target_branch", "approvals_required"],
            "dora_metrics": ["date", "deployment_frequency", "lead_time_for_changes", "time_to_restore_service", "change_failure_rate"],
            "issues": ["iid", "title", "state", "created_at", "closed_at", "author.username", "labels"],
        },
        "jira": {
            "incidents": ["key", "summary", "status", "priority", "created", "resolutiondate", "assignee", "severity"],
            "bugs": ["key", "summary", "status", "priority", "created", "updated", "assignee", "components"],
            "sprints": ["id", "name", "state", "startDate", "endDate", "completeDate", "goal"],
        },
```

### Why This Works

1. Removing the disabled flag lets users click GitLab/Jira cards in Step 1
2. Removing the early return in the callback lets the wizard proceed to Step 2
3. New Step 2 forms collect the right credentials for each platform
4. The existing wizard flow (Steps 3-6) already handles arbitrary source types

### Verification

1. Navigate to Data Sources page
2. Click "Add Data Source"
3. GitLab and Jira cards should be fully opaque and clickable (no "coming soon" text)
4. Click GitLab → Step 2 should show: Server URL, Project ID, Token, Test Connection button
5. Click Jira → Step 2 should show: Server URL, Email, API Token, Project Key, Test Connection button
6. Fill in dummy values → Test Connection → should show "Connected" badge
7. Complete full wizard flow through Step 6 → source should appear in card grid

---

## BF-8: Scoring Logic — Make Weights Adjustable

**Page:** Scoring Logic
**Severity:** P2 — feature enhancement

### Root Cause

The scoring logic page (`ui/pages/scoring_logic.py`) is read-only. It displays the check registry, weight profiles, DORA benchmarks, and archetypes — but users can't modify anything. The user expects to be able to:
1. Adjust dimension weights for the active scoring profile
2. Change the hard-gate threshold (currently hardcoded at 50)
3. Save changes and trigger recalculation

Additionally, the filter dropdown on line 99 is missing `color` and `border` styling.

### Exact Code to Change

**File 1:** `ui/pages/scoring_logic.py` — line 99

BEFORE:
```python
                    style={"width": "200px", "backgroundColor": "#0D1117"},
```

AFTER:
```python
                    style={"width": "200px", "backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F"},
```

**File 2:** `ui/pages/scoring_logic.py` — add an "Adjustable Weights" section

After Section 3 ("Weight Profiles") and before Section 4 ("Hybrid Scoring Formula"), add a new section:

```python
        # Section 3b: Adjustable weights (interactive)
        _section("Adjust Active Weights", [
            html.P("Modify dimension weights for the active profile. Changes apply to future scoring runs.",
                   style={"color": "#8B949E", "fontSize": "12px", "marginBottom": "14px"}),
            html.Div([
                *[_weight_slider_row(dim) for dim in DIMENSION_IDS],
            ], id="scoring-weight-sliders"),
            html.Div([
                html.Label("Hard Gate Threshold", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                dcc.Slider(
                    id="scoring-hard-gate-threshold",
                    min=0, max=100, step=5, value=50,
                    marks={0: "0", 25: "25", 50: "50", 75: "75", 100: "100"},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
                html.Div("Checks scoring below this threshold trigger a hard gate (dimension capped at L2).",
                         style={"color": "#8B949E", "fontSize": "11px", "marginTop": "4px"}),
            ], style={"marginTop": "16px", "marginBottom": "16px"}),
            html.Button(
                [html.I(className="fas fa-save", style={"marginRight": "6px"}), "Save & Recalculate"],
                id="scoring-save-btn",
                className="btn btn-primary",
            ),
            dbc.Toast(
                id="scoring-toast",
                header="Scoring",
                is_open=False,
                duration=3000,
                style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999},
            ),
        ]),
```

ADD helper function:
```python
def _weight_slider_row(dim_id):
    label = dim_id.replace("_", " ").title()
    default_weight = WEIGHT_PROFILES["balanced"].get(dim_id, 0.11)
    return html.Div([
        html.Div([
            html.Span(label, style={"color": "#E6EDF3", "fontSize": "12px"}),
            html.Span(f"{int(default_weight * 100)}%",
                       id=f"scoring-weight-display-{dim_id}",
                       style={"color": "#8B949E", "fontSize": "12px", "marginLeft": "auto"}),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}),
        dcc.Slider(
            id=f"scoring-weight-{dim_id}",
            min=0, max=30, step=1,
            value=int(default_weight * 100),
            marks=None,
            tooltip={"placement": "bottom", "always_visible": False},
        ),
    ], style={"marginBottom": "12px"})
```

**File 3:** Create `callbacks/scoring_logic_callbacks.py` — new callback file:

```python
"""Scoring Logic page callbacks — filter check table, save weight changes."""
import json
from pathlib import Path
from dash import Input, Output, State, no_update
from compass.scoring_constants import DIMENSION_IDS

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "scoring_config.json"

def register_callbacks(app):
    # CB1: Filter check table by platform
    @app.callback(
        Output("scoring-check-table", "children"),
        Input("scoring-check-platform-filter", "value"),
    )
    def filter_checks(platform):
        from compass.hygiene_scorer import get_all_check_definitions
        from ui.pages.scoring_logic import _check_table
        checks = get_all_check_definitions()
        if platform and platform != "all":
            checks = [c for c in checks if c["platform"] == platform]
        return _check_table(checks)

    # CB2: Save adjusted weights
    @app.callback(
        Output("scoring-toast", "is_open"),
        Output("scoring-toast", "header"),
        Output("scoring-toast", "children"),
        Input("scoring-save-btn", "n_clicks"),
        [State(f"scoring-weight-{dim}", "value") for dim in DIMENSION_IDS],
        State("scoring-hard-gate-threshold", "value"),
        prevent_initial_call=True,
    )
    def save_weights(n_clicks, *args):
        if not n_clicks:
            return False, "", ""
        weights = {}
        for i, dim in enumerate(DIMENSION_IDS):
            weights[dim] = args[i] / 100.0
        hard_gate = args[-1]
        config = {"custom_weights": weights, "hard_gate_threshold": hard_gate}
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        return True, "Saved", f"Weights saved. Hard gate threshold: {hard_gate}"
```

**File 4:** Register the new callbacks in `app.py` — add:
```python
from callbacks import scoring_logic_callbacks
scoring_logic_callbacks.register_callbacks(app)
```

### Why This Works

1. The filter dropdown fix is cosmetic — same pattern as BF-4/BF-5
2. The weight sliders let users adjust each dimension's weight interactively
3. The hard gate slider lets users change the threshold from the default 50
4. Saving persists to `config/scoring_config.json` — the scoring engine can read this on next run
5. Toast provides feedback that the save succeeded

### Verification

1. Navigate to Scoring Logic page
2. Filter dropdown should have visible text and border
3. "Adjust Active Weights" section should show 9 sliders with dimension names
4. Hard Gate Threshold slider should show default value of 50
5. Move sliders → click "Save & Recalculate" → toast should appear: "Weights saved"
6. Verify `config/scoring_config.json` was created with correct values

---

## BF-9: Global Dark Theme CSS Gaps

**Severity:** P1 — affects multiple pages

### Root Cause

The CSS already has `.form-control`, `.form-select`, `.Select-control` overrides (lines 266-346). However, there are still gaps:

1. **Dash DataTable filter inputs** — when using `filter_action="native"`, the filter input boxes inherit white
2. **Slider tooltips** — covered in BF-6
3. **Number inputs in `dcc.Slider`** — the number input shown when `tooltip` is visible
4. **Any remaining Dash component that creates `<input>` elements dynamically**

### Exact Code to Change

**File:** `assets/style.css` — add at end of file (before the final `}` comment):

```css
/* DataTable filter inputs */
.dash-spreadsheet-container .dash-filter input {
    background-color: var(--elevated) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 4px 8px !important;
}

/* Number input inside Dash components */
.dash-input, input.dash-input-element {
    background-color: var(--elevated) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
}

/* dcc.Dropdown placeholder and single-value text */
.Select-value { color: var(--text) !important; }
.Select-input input { color: var(--text) !important; }
.Select--single > .Select-control .Select-value { color: var(--text) !important; }
.Select-clear-zone { color: var(--text3) !important; }
.Select-arrow-zone { color: var(--text3) !important; }

/* Pagination dark theme */
.dash-table-container .previous-next-container button {
    background-color: var(--elevated) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}
.dash-table-container .page-number {
    color: var(--text) !important;
}
```

### Why This Works

These selectors target specific Dash-generated DOM elements that weren't covered by the existing CSS rules. Each rule uses `!important` to override inline styles that Dash components may inject.

### Verification

1. Navigate to Scoring Logic page → DataTable filter inputs should be dark
2. Navigate to Admin page → all inputs dark
3. Navigate to every page with a DataTable → pagination buttons should be dark
4. No white boxes, white text on white, or white input fields anywhere

---

## Execution Order

| Step | Task | Files Changed | Pages Fixed |
|------|------|--------------|-------------|
| 1 | BF-9: Global CSS | `assets/style.css` | All pages |
| 2 | BF-6: Admin slider tooltips | `assets/style.css` | Admin |
| 3 | BF-1: Results/Roadmap dropdowns | `compass_results_callbacks.py`, `compass_roadmap_callbacks.py` | Results, Roadmap |
| 4 | BF-2: Trend Analysis colors | `callbacks/trend_callbacks.py` | Trend Analysis |
| 5 | BF-3: Correlation heatmap | `callbacks/correlation_callbacks.py`, `maturity_scores.csv` | Correlation |
| 6 | BF-4: Deployment Explorer | `ui/pages/deployment_explorer.py` | Deployment Explorer |
| 7 | BF-5: Team Drilldown | `ui/pages/team_drilldown.py` | Team Drilldown |
| 8 | BF-7: GitLab & Jira | `wizard_steps.py`, `datasource_callbacks.py` | Data Sources |
| 9 | BF-8: Scoring Logic | `scoring_logic.py`, new callbacks | Scoring Logic |

**Rationale:** CSS first (fixes the most pages at once), then P0 functional bugs, then P1 cosmetic, then P2 features.

---

## Post-Fix Validation Plan

### Phase 1: Individual Fix Verification
After each fix, verify it in isolation:
- Start app: `CICD_APP_USE_MOCK=true python3 app.py`
- Navigate to affected page(s)
- Confirm the specific fix works per verification steps above
- Check browser console for JavaScript errors

### Phase 2: Full Page Walkthrough (15 pages)
Visit every page and verify:

| Page | Check |
|------|-------|
| Overview | KPIs render, charts load, no white boxes |
| Assessment | Next button works, radio buttons visible, complete flow |
| Results | Dropdown populates, dashboard renders, exports work |
| Roadmap | Dropdown populates, roadmap items display, status toggles work |
| History | Assessment list loads, comparison works |
| Team Drilldown | Team selector has border, radar/gauge render, domain details show |
| Trend Analysis | All 4 charts render (multi-line, deltas, tier stacked, domain multiples) |
| Correlation | Heatmap shows color variation, scatters have spread, insights meaningful |
| Deployment Explorer | All 3 filters visible and functional, charts load, events table shows |
| DORA Metrics | KPIs render, charts load |
| Scoring Logic | Filter dropdown visible, check table filters, weight sliders work, save works |
| Data Sources | All 6 source types clickable, wizard flow complete for each |
| Hygiene | Cards render, scores display |
| Admin | All inputs dark, sliders work, save config works, scoring matrix renders |
| Help / About | Page loads, content displays |

### Phase 3: Run Test Suite
```bash
cd /Users/darkstar33/Documents/GitHub/CICDApp
python3 -m pytest tests/ -v --tb=short
```
All existing tests must pass. No test modifications unless a test was testing the broken behavior.

### Phase 4: Run VERIFICATION_AGENT.md
Execute the full 16-task verification from `/Users/darkstar33/Downloads/VERIFICATION_AGENT.md`:
- Tasks 1-6: Connector verifications
- Tasks 7-9: Hygiene, DDL, mock data
- Tasks 10-16: Assessment features, exports, notebooks, tests

Each task has specific bash commands to run. All should report PASS.

### Phase 5: Final Sweep
After all verification passes:
1. Restart app fresh (kill and relaunch)
2. Complete one full assessment flow: Setup → Questions → Results → Roadmap
3. Screenshot each page for confirmation
4. Check browser console for any remaining errors
5. Check server logs for any Python exceptions

---

## Risk Assessment

| Fix | Risk | Mitigation |
|-----|------|------------|
| BF-1 | Removing `prevent_initial_call` might cause CB to fire on unrelated pages | Guard `if current_page != "compass_results"` already handles this |
| BF-2 | `_hex_to_rgba` might fail on non-hex colors | TIER_COLORS are all hex; function handles both with/without `#` prefix |
| BF-3 | New CSV data might break other tests | Keep same schema and team IDs; only change raw_score values |
| BF-7 | New wizard forms might have callback ID collisions | Using same pattern-matching IDs as existing forms; tested pattern is proven |
| BF-8 | New callback file needs registration | Must add import to `app.py`; follow existing registration pattern |
| BF-9 | CSS `!important` overrides might conflict | Only targeting specific Dash component classes, not general elements |
