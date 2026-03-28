"""Pipeline Compass Assessment — Single Page Layout.
All questions displayed on one scrollable page grouped by dimension.
Two actions: SUBMIT (green) to score the assessment, SAVE (blue) to persist progress.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from compass.question_bank.loader import (
    load_all_dimensions,
    get_dimension_metadata,
    get_adaptive_questions,
)
from compass.assessment_store import get_all_assessments, get_organization
from compass.admin_config import get_admin_config


def create_layout():
    """Build the single-page assessment layout."""
    cfg = get_admin_config()
    uses_databricks = cfg.get("uses_databricks", False)
    resume_options = _build_resume_options()

    # Load all dimensions and their questions
    load_all_dimensions()
    all_meta = get_dimension_metadata()
    dims = [m for m in all_meta if not m["is_databricks"]]
    if uses_databricks:
        dims.extend(m for m in all_meta if m["is_databricks"])

    # Build question sections for every dimension
    question_sections = []
    for dim in dims:
        dim_questions = get_adaptive_questions(dim["id"], {}, uses_databricks)
        cards = [_question_card(q) for q in dim_questions]

        question_sections.append(html.Div([
            # Dimension header
            html.Div([
                html.I(className=f"fas fa-{dim.get('icon', 'circle')}", style={
                    "color": dim.get("color", "#4B7BF5"), "fontSize": "20px",
                }),
                html.Div([
                    html.Div(dim["display_name"], style={
                        "color": "#E6EDF3", "fontSize": "16px", "fontWeight": "700",
                    }),
                    html.Div(dim.get("description", ""), style={
                        "color": "#8B949E", "fontSize": "12px",
                    }),
                ]),
            ], style={
                "display": "flex", "alignItems": "center", "gap": "12px",
                "marginBottom": "16px", "paddingBottom": "12px",
                "borderBottom": f"2px solid {dim.get('color', '#4B7BF5')}44",
            }),
            # Questions
            html.Div(cards),
        ], style={"marginBottom": "32px"}))

    return html.Div([
        # Page title
        html.Div([
            html.Div([
                html.I(className="fas fa-compass", style={"color": "#4B7BF5", "fontSize": "22px"}),
                html.Div([
                    html.Div("Pipeline Compass Assessment", style={
                        "fontSize": "20px", "fontWeight": "700", "color": "#E6EDF3",
                    }),
                    html.Div("CI/CD Maturity Assessment — answer all questions below", style={
                        "fontSize": "12px", "color": "#8B949E",
                    }),
                ]),
            ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
        ], style={"marginBottom": "24px"}),

        # Setup form (team info)
        _setup_form(resume_options),

        # Status area — shows feedback after submit/save
        html.Div(id="compass-status-area"),

        # All questions
        html.Div(question_sections, id="compass-questions-container", style={
            "marginTop": "24px",
        }),

        # ============================================================
        # ACTION BUTTONS
        # ============================================================
        html.Div([
            html.Button("SAVE PROGRESS", id="compass-save-btn", n_clicks=0, style={
                "backgroundColor": "#3B82F6",
                "color": "#FFFFFF",
                "border": "none",
                "borderRadius": "8px",
                "padding": "14px 36px",
                "fontSize": "16px",
                "fontWeight": "700",
                "cursor": "pointer",
                "textTransform": "uppercase",
                "letterSpacing": "1px",
            }),
            html.Button("SUBMIT ASSESSMENT", id="compass-submit-btn", n_clicks=0, style={
                "backgroundColor": "#22C55E",
                "color": "#FFFFFF",
                "border": "none",
                "borderRadius": "8px",
                "padding": "14px 36px",
                "fontSize": "16px",
                "fontWeight": "700",
                "cursor": "pointer",
                "textTransform": "uppercase",
                "letterSpacing": "1px",
            }),
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "gap": "24px",
            "marginTop": "32px",
            "paddingTop": "24px",
            "paddingBottom": "40px",
            "borderTop": "2px solid var(--border, #272D3F)",
        }),
        # ============================================================
        # END ACTION BUTTONS
        # ============================================================

        # Toast notifications
        dbc.Toast(
            id="compass-toast",
            header="",
            is_open=False,
            duration=4000,
            style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999},
        ),
    ], style={"padding": "24px", "maxWidth": "900px", "margin": "0 auto"})


def _setup_form(resume_options=None):
    """Team info form at the top of the page."""
    _input_style = {
        "backgroundColor": "var(--elevated, #21262D)",
        "color": "#E6EDF3",
        "border": "1px solid var(--border, #272D3F)",
    }
    cfg = get_admin_config()
    profile_label = cfg.get("scoring_profile", "balanced").replace("_", " ").title()
    industry_label = cfg.get("industry", "tech").replace("_", " ").title()
    org_size_label = cfg.get("org_size", "mid_market").replace("_", " ").title()
    db_label = "Yes" if cfg.get("uses_databricks") else "No"

    sections = []

    # Resume section
    if resume_options:
        sections.append(html.Div([
            html.Div("Resume a Saved Assessment", style={
                "fontSize": "14px", "fontWeight": "700", "color": "#E6EDF3", "marginBottom": "8px",
            }),
            html.Div([
                dbc.Select(
                    id="compass-resume-selector",
                    options=resume_options,
                    placeholder="Select a saved assessment...",
                    style=_input_style,
                ),
                dbc.Button(
                    [html.I(className="fas fa-play"), " Resume"],
                    id="compass-resume-btn",
                    color="primary",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "8px", "whiteSpace": "nowrap"},
                ),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "backgroundColor": "var(--surface, #161B22)",
            "borderRadius": "8px",
            "padding": "16px 20px",
            "border": "1px solid var(--border, #272D3F)",
            "marginBottom": "12px",
        }))
    else:
        sections.append(html.Div([
            dbc.Select(id="compass-resume-selector", options=[], style={"display": "none"}),
            html.Div(id="compass-resume-btn", style={"display": "none"}),
        ]))

    # New assessment form
    sections.append(html.Div([
        html.Div("Your Details", style={
            "fontSize": "14px", "fontWeight": "700", "color": "#E6EDF3", "marginBottom": "12px",
        }),
        html.Div([
            html.Div([
                html.Label("Your Name *", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                dbc.Input(id="compass-respondent-name", placeholder="e.g., Jane Smith", type="text",
                          className="mt-1", style=_input_style),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Your Role *", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                dbc.Input(id="compass-respondent-role", placeholder="e.g., DevOps Lead", type="text",
                          className="mt-1", style=_input_style),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "12px"}),
        html.Div([
            html.Div([
                html.Label("Team *", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                dbc.Input(id="compass-org-name", placeholder="e.g., Data Platform Team", type="text",
                          className="mt-1", style=_input_style),
            ], style={"flex": "1"}),
            html.Div([
                html.Label("Assessment Name", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                dbc.Input(id="compass-save-name", placeholder="e.g., Q1 2026 Baseline", type="text",
                          className="mt-1", style=_input_style),
            ], style={"flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "12px"}),

        # Config summary
        html.Div([
            html.Div([
                html.I(className="fas fa-info-circle", style={"color": "#4B7BF5", "fontSize": "12px", "marginRight": "8px"}),
                html.Span("Assessment settings (change in Admin):", style={"color": "#8B949E", "fontSize": "12px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
            html.Div([
                _badge("Profile", profile_label),
                _badge("Industry", industry_label),
                _badge("Size", org_size_label),
                _badge("Databricks", db_label),
            ], style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}),
        ], style={
            "backgroundColor": "var(--elevated, #21262D)",
            "borderRadius": "6px",
            "padding": "10px 14px",
            "border": "1px solid var(--border, #272D3F)",
        }),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "20px",
        "border": "1px solid var(--border, #272D3F)",
    }))

    return html.Div(sections)


def _badge(label, value):
    return html.Span([
        html.Span(f"{label}: ", style={"color": "#484F58", "fontSize": "11px"}),
        html.Span(value, style={"color": "#E6EDF3", "fontSize": "11px", "fontWeight": "600"}),
    ], style={
        "backgroundColor": "#161B22",
        "padding": "4px 10px",
        "borderRadius": "4px",
        "border": "1px solid #272D3F",
    })


def _question_card(question, response_value=None):
    """Render a single question card based on its type."""
    qid = question["id"]
    qtype = question.get("type", "likert")
    options = question.get("options", [])
    weight = question.get("weight", 1)

    importance = html.Div([
        html.Span("Importance ", style={"color": "#484F58", "fontSize": "10px"}),
        *[html.Span("*" if i < weight else ".", style={
            "color": "#4B7BF5" if i < weight else "#272D3F", "fontSize": "10px", "marginRight": "2px",
        }) for i in range(5)],
    ], style={"marginTop": "4px"})

    if qtype in ("likert", "single_select"):
        current_val = None
        if response_value and isinstance(response_value, dict):
            current_val = response_value.get("value")

        radio_options = [{"label": o["label"], "value": o["value"]} for o in options]
        if not any(o["value"] == -1 for o in options):
            radio_options.append({"label": "I'm not sure / Don't know", "value": -1})

        control = dbc.RadioItems(
            id={"type": "compass-response", "index": qid},
            options=radio_options,
            value=current_val,
            labelStyle={
                "display": "block", "padding": "10px 14px", "marginBottom": "6px",
                "borderRadius": "6px", "border": "1px solid var(--border, #272D3F)",
                "cursor": "pointer", "fontSize": "13px", "color": "#E6EDF3",
            },
            inputStyle={"marginRight": "10px"},
        )

    elif qtype == "multi_select":
        current_vals = []
        if response_value and isinstance(response_value, dict):
            current_vals = response_value.get("values", [])

        control = dbc.Checklist(
            id={"type": "compass-response", "index": qid},
            options=[{"label": o["label"], "value": o["value"]} for o in options],
            value=current_vals,
            labelStyle={
                "display": "block", "padding": "10px 14px", "marginBottom": "6px",
                "borderRadius": "6px", "border": "1px solid var(--border, #272D3F)",
                "cursor": "pointer", "fontSize": "13px", "color": "#E6EDF3",
            },
            inputStyle={"marginRight": "10px"},
        )

    elif qtype == "binary":
        current_val = None
        if response_value and isinstance(response_value, dict):
            current_val = response_value.get("value")

        control = dbc.RadioItems(
            id={"type": "compass-response", "index": qid},
            options=[{"label": "Yes", "value": True}, {"label": "No", "value": False}],
            value=current_val,
            inline=True,
            labelStyle={
                "padding": "10px 20px", "borderRadius": "6px",
                "border": "1px solid var(--border, #272D3F)",
                "cursor": "pointer", "fontSize": "13px", "color": "#E6EDF3", "marginRight": "8px",
            },
        )

    elif qtype == "freeform":
        current_text = ""
        if response_value and isinstance(response_value, dict):
            current_text = response_value.get("text", "")

        control = dbc.Textarea(
            id={"type": "compass-response", "index": qid},
            value=current_text,
            placeholder="Enter your response...",
            style={
                "backgroundColor": "var(--elevated, #21262D)", "color": "#E6EDF3",
                "border": "1px solid var(--border, #272D3F)", "minHeight": "80px",
            },
        )
    else:
        control = html.Div("Unsupported question type", style={"color": "#F87171"})

    return html.Div([
        html.Div([
            html.Span(question["text"], style={
                "color": "#E6EDF3", "fontSize": "14px", "fontWeight": "600", "lineHeight": "1.5",
            }),
            importance,
        ], style={"marginBottom": "14px"}),
        control,
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "20px",
        "border": "1px solid var(--border, #272D3F)",
        "marginBottom": "12px",
    })


def _build_resume_options():
    """Build dropdown options for resumable assessments."""
    try:
        assessments = get_all_assessments()
    except Exception:
        return []

    options = []
    for a in assessments:
        status = a.get("status", "in_progress")
        org = get_organization(a.get("org_id", ""))
        org_name = org["name"] if org else "Unknown"
        resp_count = len(a.get("responses", {}))
        date = (a.get("completed_at") or a.get("created_at", ""))[:10]
        save_name = a.get("save_name", "")
        name_part = f"{save_name} — " if save_name else ""

        if status == "completed":
            composite = a.get("composite", {})
            score = composite.get("overall_score", 0)
            label_text = f"{name_part}{org_name} — {score:.0f}/100 — {date} (completed)"
        else:
            label_text = f"{name_part}{org_name} — {resp_count} answers — {date} (in progress)"

        options.append({"label": label_text, "value": a["id"]})
    return options
