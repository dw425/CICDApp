"""Wizard step layout functions for the Data Source Console 6-step wizard.
# ****Truth Agent Verified**** — 6 step layouts: choose source, connect, select data type,
# field mapping, test/preview, confirm/save. Pattern-matching IDs for callbacks.

All interactive elements use pattern-matching IDs so the callback
system can handle them via a single ``{"type": "wz-action", ...}``
handler — no static IDs to pre-exist in the layout.
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

from config.data_source_slots import DATA_SOURCE_SLOTS, get_slot_choices


# ── Step indicator ────────────────────────────────────────────────

STEP_LABELS = [
    "Source Type",
    "Connect",
    "Data & Slot",
    "Field Mapping",
    "Preview",
    "Confirm",
]


def create_step_indicator(current_step=1):
    """Horizontal stepper showing progress through 6 wizard steps."""
    items = []
    for i, label in enumerate(STEP_LABELS, 1):
        if i < current_step:
            cls = "wizard-step completed"
            icon = html.I(className="fas fa-check")
        elif i == current_step:
            cls = "wizard-step active"
            icon = html.Span(str(i))
        else:
            cls = "wizard-step pending"
            icon = html.Span(str(i))

        items.append(html.Div([
            html.Div(icon, className="wizard-step-circle"),
            html.Div(label, className="wizard-step-label"),
        ], className=cls))

        if i < len(STEP_LABELS):
            items.append(html.Div(className="wizard-step-connector"))

    return html.Div(items, className="wizard-stepper")


# ── Step 1: Choose Source Type ────────────────────────────────────

SOURCE_TYPES = [
    {"id": "databricks_table", "label": "Databricks Table", "icon": "fas fa-database",
     "desc": "Unity Catalog table — introspect schema, map fields, generate SQL"},
    {"id": "azure_devops", "label": "Azure DevOps", "icon": "fab fa-microsoft",
     "desc": "Pipelines, releases, PRs, and work items via REST API"},
    {"id": "github", "label": "GitHub", "icon": "fab fa-github",
     "desc": "Actions workflows, pull requests, issues, deployments"},
    {"id": "gitlab", "label": "GitLab", "icon": "fab fa-gitlab",
     "desc": "CI pipelines, merge requests, issues (coming soon)"},
    {"id": "jira", "label": "Jira", "icon": "fab fa-jira",
     "desc": "Issues, sprints, work items (coming soon)"},
    {"id": "csv_upload", "label": "CSV Upload", "icon": "fas fa-file-csv",
     "desc": "Upload a CSV file and map columns to a CI/CD data slot"},
]


def render_step_1():
    """Step 1: Choose Source Type — grid of clickable cards."""
    cards = []
    for st in SOURCE_TYPES:
        disabled = st["id"] in ("gitlab", "jira")
        card = html.Div([
            html.I(className=st["icon"], style={"fontSize": "28px", "color": "var(--accent)", "marginBottom": "10px"}),
            html.Div(st["label"], style={"fontWeight": "600", "fontSize": "14px", "marginBottom": "4px"}),
            html.Div(st["desc"], style={"fontSize": "11px", "color": "var(--text2)", "lineHeight": "1.4"}),
        ],
            className="source-type-card disabled" if disabled else "source-type-card",
            id={"type": "wz-action", "index": f"select-source-{st['id']}"},
            style={"opacity": "0.4", "cursor": "not-allowed"} if disabled else {},
        )
        cards.append(card)

    return html.Div([
        html.Div("Select a source type", className="wizard-section-title"),
        html.Div(cards, className="source-type-grid"),
    ])


# ── Step 2: Connect & Authenticate ───────────────────────────────

def render_step_2(source_type=None, state=None):
    """Step 2: Connection/authentication form based on source_type."""
    state = state or {}

    if source_type == "databricks_table":
        return _render_step_2_databricks(state)
    elif source_type == "csv_upload":
        return _render_step_2_csv(state)
    elif source_type in ("azure_devops", "github"):
        return _render_step_2_api(source_type, state)
    else:
        return html.Div("Select a source type in Step 1.", style={"color": "var(--text2)", "padding": "20px"})


def _render_step_2_databricks(state):
    """Databricks Table connection form."""
    columns = state.get("introspect_columns", [])

    result_content = None
    if columns:
        result_content = html.Div([
            html.Div([
                html.I(className="fas fa-check-circle", style={"color": "var(--green)", "marginRight": "6px"}),
                html.Span(f"Found {len(columns)} columns", style={"fontSize": "13px", "color": "var(--green)"}),
            ], style={"marginBottom": "10px"}),
            _render_column_table(columns),
        ])

    return html.Div([
        html.Div("Databricks Unity Catalog Table", className="wizard-section-title"),
        html.Div([
            html.Label("Table path (catalog.schema.table)", style={"fontSize": "12px", "color": "var(--text2)", "marginBottom": "4px"}),
            dbc.Input(
                id={"type": "wz-input", "index": "uc-table-path"},
                placeholder="e.g. lho_analytics.cicd.deployment_events",
                value=state.get("table_path", ""),
                style={"marginBottom": "12px"},
            ),
            html.Button(
                [html.I(className="fas fa-search"), " Introspect Table"],
                id={"type": "wz-action", "index": "introspect-table"},
                className="btn btn-primary",
            ),
        ]),
        html.Div(result_content, style={"marginTop": "16px"}),
    ])


def _render_column_table(columns):
    """Render introspected column list as a DataTable."""
    if not columns:
        return None
    return dash_table.DataTable(
        columns=[
            {"name": "Column", "id": "col_name"},
            {"name": "Type", "id": "data_type"},
            {"name": "Nullable", "id": "nullable"},
        ],
        data=columns,
        style_header={"backgroundColor": "var(--elevated)", "color": "var(--text2)", "fontWeight": "600", "fontSize": "11px"},
        style_cell={"backgroundColor": "var(--surface)", "color": "var(--text)", "border": "1px solid var(--border)", "fontSize": "12px", "padding": "6px 10px"},
        style_table={"maxHeight": "250px", "overflowY": "auto"},
    )


def _render_step_2_csv(state):
    """CSV upload form."""
    preview_content = None
    if state.get("csv_data"):
        df_cols = state.get("csv_columns", [])
        preview_content = html.Div([
            html.Div([
                html.I(className="fas fa-check-circle", style={"color": "var(--green)", "marginRight": "6px"}),
                html.Span(
                    f"Parsed {state.get('csv_filename', 'file')}: {len(state['csv_data'])} rows, {len(df_cols)} columns",
                    style={"fontSize": "13px", "color": "var(--green)"},
                ),
            ], style={"marginBottom": "10px"}),
            dash_table.DataTable(
                columns=[{"name": c, "id": c} for c in df_cols],
                data=state["csv_data"][:10],
                style_header={"backgroundColor": "var(--elevated)", "color": "var(--text2)", "fontWeight": "600", "fontSize": "11px"},
                style_cell={"backgroundColor": "var(--surface)", "color": "var(--text)", "border": "1px solid var(--border)", "fontSize": "12px", "padding": "6px 10px", "maxWidth": "150px", "overflow": "hidden", "textOverflow": "ellipsis"},
                style_table={"maxHeight": "250px", "overflowY": "auto", "overflowX": "auto"},
            ),
        ])

    return html.Div([
        html.Div("Upload CSV File", className="wizard-section-title"),
        dcc.Upload(
            id={"type": "wz-upload", "index": "csv-file"},
            children=html.Div([
                html.I(className="fas fa-cloud-upload-alt", style={"fontSize": "32px", "color": "var(--text3)", "marginBottom": "8px"}),
                html.Div("Drag and drop or click to select a CSV file"),
            ]),
            className="upload-area",
            style={"padding": "40px"},
        ),
        html.Div(preview_content, style={"marginTop": "16px"}),
    ])


def _render_step_2_api(source_type, state):
    """API credential form for ADO / GitHub."""
    test_result = state.get("connection_test_result")

    if source_type == "azure_devops":
        fields = [
            ("api-org-url", "Organization URL", "https://dev.azure.com/myorg", "org_url"),
            ("api-project", "Project Name", "MyProject", "project"),
            ("api-pat", "Personal Access Token", "Paste your PAT", "pat"),
        ]
        title = "Azure DevOps Connection"
    else:
        fields = [
            ("api-owner", "Owner / Organization", "my-org", "owner"),
            ("api-repo", "Repository (optional — leave blank for org-wide)", "my-repo", "repo"),
            ("api-token", "Personal Access Token", "ghp_...", "token"),
        ]
        title = "GitHub Connection"

    form_items = []
    for field_idx, label, placeholder, key in fields:
        is_secret = key in ("pat", "token")
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


# ── Step 3: Select Data Type & CI/CD Slot ────────────────────────

def render_step_3(source_type=None, state=None):
    """Step 3: Pick data type and target CI/CD slot."""
    state = state or {}
    slot_options = [{"label": v["label"], "value": k} for k, v in DATA_SOURCE_SLOTS.items()]
    data_type_options = _get_data_type_options(source_type)

    # Canonical fields preview
    slot_id = state.get("slot_id")
    fields_preview = None
    if slot_id:
        from config.data_source_slots import get_all_fields
        fields = get_all_fields(slot_id)
        rows = []
        for f in fields:
            req_badge = html.Span("Required", className="badge critical", style={"fontSize": "10px"}) if f["required"] \
                else html.Span("Optional", className="badge neutral", style={"fontSize": "10px"})
            rows.append(html.Tr([
                html.Td(f["name"], style={"fontSize": "12px"}),
                html.Td(f["type"], style={"fontSize": "12px", "color": "var(--text2)"}),
                html.Td(req_badge),
                html.Td(f["description"], style={"fontSize": "11px", "color": "var(--text2)"}),
            ]))
        fields_preview = html.Div([
            html.Div("Expected Canonical Fields", style={
                "fontSize": "12px", "fontWeight": "600", "color": "var(--text2)",
                "marginBottom": "8px", "textTransform": "uppercase", "letterSpacing": "0.5px",
            }),
            html.Table([
                html.Thead(html.Tr([html.Th("Field"), html.Th("Type"), html.Th("Required"), html.Th("Description")],
                                    style={"fontSize": "11px"})),
                html.Tbody(rows),
            ], className="data-table"),
        ])

    return html.Div([
        html.Div("Select Data Type & CI/CD Slot", className="wizard-section-title"),
        html.Div([
            html.Div([
                html.Label("What data are you pulling?", style={"fontSize": "12px", "color": "var(--text2)", "marginBottom": "6px", "display": "block"}),
                dcc.Dropdown(
                    id={"type": "wz-dropdown", "index": "data-type"},
                    options=data_type_options,
                    value=state.get("data_type"),
                    placeholder="Select data type...",
                    style={"marginBottom": "12px"},
                ),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Which CI/CD slot does this fill?", style={"fontSize": "12px", "color": "var(--text2)", "marginBottom": "6px", "display": "block"}),
                dcc.Dropdown(
                    id={"type": "wz-dropdown", "index": "slot-id"},
                    options=slot_options,
                    value=state.get("slot_id"),
                    placeholder="Select target slot...",
                    style={"marginBottom": "12px"},
                ),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "24px"}),
        # Apply button to update state
        html.Button(
            [html.I(className="fas fa-check"), " Apply Selection"],
            id={"type": "wz-action", "index": "update-slot"},
            className="btn btn-secondary",
            style={"marginTop": "8px", "marginBottom": "16px"},
        ),
        fields_preview,
    ])


def _get_data_type_options(source_type):
    if source_type == "azure_devops":
        return [
            {"label": "Pipelines (Builds)", "value": "pipelines"},
            {"label": "Releases", "value": "releases"},
            {"label": "Pull Requests", "value": "pull_requests"},
            {"label": "Work Items", "value": "work_items"},
        ]
    elif source_type == "github":
        return [
            {"label": "Workflow Runs", "value": "workflows"},
            {"label": "Pull Requests", "value": "pull_requests"},
            {"label": "Issues", "value": "issues"},
            {"label": "Deployments", "value": "deployments"},
        ]
    elif source_type == "databricks_table":
        return [{"label": "Table data (as-is)", "value": "table"}]
    elif source_type == "csv_upload":
        return [{"label": "CSV data (as-is)", "value": "csv"}]
    return []


# ── Step 4: Field Mapping ─────────────────────────────────────────

def render_step_4(state=None):
    """Step 4: Two-column mapping table (source → canonical)."""
    state = state or {}
    slot_id = state.get("slot_id")
    source_columns = state.get("source_columns", [])
    field_mapping = state.get("field_mapping", {})

    if not slot_id:
        return html.Div("Select a CI/CD slot in Step 3 first.", style={"color": "var(--text2)", "padding": "20px"})

    slot = DATA_SOURCE_SLOTS.get(slot_id, {})
    canonical_fields = [f["name"] for f in slot.get("fields", [])]
    canonical_options = [{"label": "— skip —", "value": ""}] + [{"label": f, "value": f} for f in canonical_fields]

    mapping_rows = []
    for col in source_columns:
        mapped_to = field_mapping.get(col, "")
        mapping_rows.append(
            html.Div([
                html.Div(col, style={"flex": "1", "fontSize": "13px", "color": "var(--text)", "padding": "8px 0"}),
                html.Div(html.I(className="fas fa-arrow-right", style={"color": "var(--text3)"}), style={"padding": "8px 12px"}),
                html.Div(
                    dcc.Dropdown(
                        id={"type": "wz-dropdown", "index": f"fmap-{col}"},
                        options=canonical_options,
                        value=mapped_to,
                        placeholder="Map to...",
                        clearable=True,
                        style={"width": "100%"},
                    ),
                    style={"flex": "1"},
                ),
            ], style={"display": "flex", "alignItems": "center", "borderBottom": "1px solid var(--border)", "padding": "4px 0"})
        )

    # SQL preview for Databricks tables
    sql_preview = None
    source_type = state.get("source_type")
    if source_type == "databricks_table" and field_mapping:
        sql = _generate_sql_preview(state)
        sql_preview = html.Div([
            html.Div("Generated SQL", className="wizard-section-title", style={"marginTop": "16px"}),
            html.Pre(sql, style={
                "background": "var(--bg)", "padding": "12px", "borderRadius": "8px",
                "fontSize": "12px", "color": "var(--green)", "border": "1px solid var(--border)",
                "maxHeight": "200px", "overflowY": "auto",
            }),
            html.Div([
                html.Label("WHERE clause (optional)", style={"fontSize": "12px", "color": "var(--text2)", "display": "block", "marginTop": "8px"}),
                dbc.Input(
                    id={"type": "wz-input", "index": "where-clause"},
                    placeholder="e.g. event_date >= '2024-01-01'",
                    value=state.get("where_clause", ""),
                ),
            ]),
        ])

    return html.Div([
        html.Div([
            html.Div("Map Source Fields to Canonical Schema", className="wizard-section-title"),
            html.Button(
                [html.I(className="fas fa-magic"), " Auto-Map"],
                id={"type": "wz-action", "index": "auto-map"},
                className="btn btn-secondary",
                style={"fontSize": "11px"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        html.Div([
            html.Div("Source Field", style={"flex": "1", "fontSize": "11px", "fontWeight": "600", "color": "var(--text2)", "textTransform": "uppercase", "letterSpacing": "0.5px"}),
            html.Div("", style={"width": "44px"}),
            html.Div("Canonical Field", style={"flex": "1", "fontSize": "11px", "fontWeight": "600", "color": "var(--text2)", "textTransform": "uppercase", "letterSpacing": "0.5px"}),
        ], style={"display": "flex", "borderBottom": "1px solid var(--border)", "padding": "8px 0"}),
        html.Div(mapping_rows, style={"maxHeight": "300px", "overflowY": "auto"}),
        html.Button(
            [html.I(className="fas fa-save"), " Apply Mapping"],
            id={"type": "wz-action", "index": "update-mapping"},
            className="btn btn-secondary",
            style={"marginTop": "12px", "fontSize": "11px"},
        ),
        sql_preview,
    ])


def _generate_sql_preview(state):
    table_path = state.get("table_path", "<table>")
    mapping = state.get("field_mapping", {})
    where = state.get("where_clause", "")
    select_parts = []
    for src, dst in mapping.items():
        if dst:
            select_parts.append(f"  {src} AS {dst}" if src != dst else f"  {src}")
    if not select_parts:
        return f"SELECT *\nFROM {table_path}"
    sql = "SELECT\n" + ",\n".join(select_parts) + f"\nFROM {table_path}"
    if where:
        sql += f"\nWHERE {where}"
    sql += "\nLIMIT 25"
    return sql


# ── Step 5: Test & Preview ────────────────────────────────────────

def render_step_5(state=None):
    """Step 5: Preview table + validation checklist."""
    state = state or {}
    preview_data = state.get("preview_data", [])
    preview_columns = state.get("preview_columns", [])
    validation_results = state.get("validation_results", [])

    table = None
    if preview_data and preview_columns:
        table = dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in preview_columns],
            data=preview_data[:25],
            style_header={"backgroundColor": "var(--elevated)", "color": "var(--text2)", "fontWeight": "600", "fontSize": "11px"},
            style_cell={"backgroundColor": "var(--surface)", "color": "var(--text)", "border": "1px solid var(--border)", "fontSize": "12px", "padding": "6px 10px", "maxWidth": "200px", "overflow": "hidden", "textOverflow": "ellipsis"},
            style_table={"maxHeight": "350px", "overflowY": "auto", "overflowX": "auto"},
            page_size=25,
        )

    checks = []
    for v in validation_results:
        icon = "fas fa-check-circle" if v.get("passed") else "fas fa-times-circle"
        color = "var(--green)" if v.get("passed") else "var(--red)"
        checks.append(html.Div([
            html.I(className=icon, style={"color": color, "marginRight": "8px"}),
            html.Span(v.get("message", ""), style={"fontSize": "13px"}),
        ], style={"marginBottom": "6px"}))

    return html.Div([
        html.Div([
            html.Div("Test & Preview", className="wizard-section-title"),
            html.Button(
                [html.I(className="fas fa-play"), " Run Preview"],
                id={"type": "wz-action", "index": "run-preview"},
                className="btn btn-primary",
                style={"fontSize": "11px"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        html.Div(table, style={"marginTop": "16px"}),
        html.Div([
            html.Div("Validation", className="wizard-section-title", style={"marginTop": "16px"}) if checks else None,
            *checks,
        ]),
    ])


# ── Step 6: Confirm & Save ────────────────────────────────────────

def render_step_6(state=None):
    """Step 6: Summary card + save buttons."""
    state = state or {}
    source_type = state.get("source_type", "")
    slot_id = state.get("slot_id", "")
    data_type = state.get("data_type", "")
    field_mapping = state.get("field_mapping", {})
    mapped_count = sum(1 for v in field_mapping.values() if v)

    slot_label = DATA_SOURCE_SLOTS.get(slot_id, {}).get("label", slot_id)
    target_table = DATA_SOURCE_SLOTS.get(slot_id, {}).get("target_table", "")

    type_labels = {
        "databricks_table": "Databricks Table",
        "azure_devops": "Azure DevOps",
        "github": "GitHub",
        "csv_upload": "CSV Upload",
    }

    return html.Div([
        html.Div("Confirm & Save", className="wizard-section-title"),
        html.Div([
            html.Label("Source Name", style={"fontSize": "12px", "color": "var(--text2)", "marginBottom": "4px", "display": "block"}),
            dbc.Input(
                id={"type": "wz-input", "index": "source-name"},
                placeholder="e.g. GitHub PRs - Platform Team",
                value=state.get("source_name", ""),
                style={"marginBottom": "16px"},
            ),
        ]),
        html.Div([
            _summary_row("Source Type", type_labels.get(source_type, source_type)),
            _summary_row("Data Type", data_type),
            _summary_row("CI/CD Slot", slot_label),
            _summary_row("Target Table", target_table),
            _summary_row("Fields Mapped", f"{mapped_count} fields"),
        ], className="card", style={"padding": "16px", "marginBottom": "20px"}),
        html.Div([
            html.Button(
                [html.I(className="fas fa-check"), " Save & Activate"],
                id={"type": "wz-action", "index": "save-activate"},
                className="btn btn-primary",
                style={"marginRight": "12px"},
            ),
            html.Button(
                [html.I(className="fas fa-save"), " Save as Draft"],
                id={"type": "wz-action", "index": "save-draft"},
                className="btn btn-secondary",
            ),
        ]),
    ])


def _summary_row(label, value):
    return html.Div([
        html.Span(label, style={"fontSize": "12px", "color": "var(--text2)", "width": "140px", "display": "inline-block"}),
        html.Span(value or "—", style={"fontSize": "13px", "fontWeight": "500", "color": "var(--text)"}),
    ], style={"marginBottom": "8px"})
