"""Callbacks for Pipeline Compass Assessment Wizard.
# CB0: reset wizard stores on page entry (prevents stale session state).
# CB1: clientside response capture. CB2: full navigation
# (setup→questions→complete, Next/Back/Resume/Save). CB3: autosave every 30s.
# CB4: completion screen nav (goto-results/roadmap).
"""

from datetime import datetime
from dash import html, Input, Output, State, ctx, no_update, ALL
import dash_bootstrap_components as dbc

from compass.question_bank.loader import (
    load_all_dimensions,
    get_dimension_metadata,
    get_adaptive_questions,
    get_question_count,
    get_dimension_ids,
    get_databricks_dimensions,
    get_question,
)
from compass.assessment_store import (
    create_organization,
    create_assessment,
    get_assessment,
    get_organization,
    save_response,
    save_scores,
    get_responses,
    update_assessment,
)
from compass.scoring_engine import (
    full_score_assessment,
    TIER_COLORS,
)
from compass.antipattern_engine import detect_anti_patterns
from compass.roadmap_engine import generate_roadmap
from compass.benchmark_data import compare_to_benchmarks
from compass.admin_config import get_admin_config
from ui.pages.compass_assessment import create_question_card


def register_callbacks(app):
    """Register all compass assessment callbacks."""

    # ── CB0: Reset wizard stores when navigating TO the assessment page ──
    # Prevents stale session storage from breaking the wizard flow.
    # Users can resume saved assessments via the Resume button.
    @app.callback(
        Output("compass-wizard-step", "data", allow_duplicate=True),
        Output("compass-current-dim", "data", allow_duplicate=True),
        Output("compass-responses", "data", allow_duplicate=True),
        Output("compass-live-answers", "data", allow_duplicate=True),
        Output("compass-config", "data", allow_duplicate=True),
        Output("compass-assessment-id", "data", allow_duplicate=True),
        Output("compass-org-id", "data", allow_duplicate=True),
        Input("current-page", "data"),
        prevent_initial_call=True,
    )
    def reset_wizard_on_page_entry(current_page):
        """Reset all wizard stores to initial state when entering the assessment page."""
        if current_page == "compass_assessment":
            return "setup", 0, {}, {}, {}, None, None
        return (no_update,) * 7

    # ── CB1: Client-side callback to capture responses into store ──
    # Runs in the browser — no server round-trip, no output conflicts.
    app.clientside_callback(
        """
        function(values, ids, existing) {
            if (!values || !ids || values.length === 0) {
                return window.dash_clientside.no_update;
            }
            var result = Object.assign({}, existing || {});
            for (var i = 0; i < values.length; i++) {
                var val = values[i];
                if (val === null || val === undefined) continue;
                var qid = ids[i].index;
                if (Array.isArray(val)) {
                    result[qid] = {response_type: "multi_select", response_value: {values: val}};
                } else if (typeof val === "boolean") {
                    result[qid] = {response_type: "binary", response_value: {value: val}};
                } else if (typeof val === "string" && val.length > 20) {
                    result[qid] = {response_type: "freeform", response_value: {text: val}};
                } else {
                    result[qid] = {response_type: "likert", response_value: {value: val}};
                }
            }
            return result;
        }
        """,
        Output("compass-live-answers", "data"),
        Input({"type": "compass-response", "index": ALL}, "value"),
        State({"type": "compass-response", "index": ALL}, "id"),
        State("compass-live-answers", "data"),
        prevent_initial_call=True,
    )

    # ── CB2: Main navigation (Next / Back / Resume / Save) ──
    @app.callback(
        Output("compass-content", "children"),
        Output("compass-progress-bar", "style"),
        Output("compass-progress-text", "children"),
        Output("compass-dim-tabs", "children"),
        Output("compass-back-btn", "style"),
        Output("compass-save-btn", "style"),
        Output("compass-next-btn", "children"),
        Output("compass-wizard-step", "data"),
        Output("compass-assessment-id", "data"),
        Output("compass-org-id", "data"),
        Output("compass-current-dim", "data"),
        Output("compass-responses", "data"),
        Output("compass-config", "data"),
        Output("compass-toast", "is_open"),
        Output("compass-toast", "header"),
        Output("compass-toast", "children"),
        Output("selected-assessment-id", "data"),
        Input("compass-next-btn", "n_clicks"),
        Input("compass-back-btn", "n_clicks"),
        Input("compass-resume-btn", "n_clicks"),
        Input("compass-save-btn", "n_clicks"),
        State("compass-wizard-step", "data"),
        State("compass-assessment-id", "data"),
        State("compass-org-id", "data"),
        State("compass-current-dim", "data"),
        State("compass-responses", "data"),
        State("compass-config", "data"),
        State("compass-live-answers", "data"),
        State("compass-org-name", "value"),
        State("compass-respondent-name", "value"),
        State("compass-respondent-role", "value"),
        State("compass-save-name", "value"),
        State("compass-resume-selector", "value"),
        prevent_initial_call=True,
    )
    def handle_navigation(
        next_clicks, back_clicks, resume_clicks, save_clicks,
        step, assessment_id, org_id, current_dim, responses, config,
        live_answers,
        team_name, respondent_name, respondent_role, save_name,
        resume_id,
    ):
        triggered = ctx.triggered_id
        if not triggered:
            return _no_update()

        responses = responses or {}
        config = config or {}
        live_answers = live_answers or {}
        current_dim = current_dim or 0

        # Merge live answers into responses
        if live_answers:
            responses.update(live_answers)

        cfg_databricks = config.get("uses_databricks", False)

        # ── Resume button ──
        if triggered == "compass-resume-btn":
            if not resume_id:
                return _toast_only("Select Assessment", "Please select an assessment to resume.")

            assessment = get_assessment(resume_id)
            if not assessment:
                return _toast_only("Error", "Assessment not found.")

            a_responses = {}
            raw_responses = assessment.get("responses", {})
            for qid, r in raw_responses.items():
                a_responses[qid] = {
                    "response_type": r.get("response_type", "likert"),
                    "response_value": r.get("response_value", {}),
                }

            org = get_organization(assessment.get("org_id", ""))
            a_config = {
                "uses_databricks": org.get("uses_databricks", False) if org else False,
                "weight_profile": assessment.get("weight_profile", "balanced"),
                "industry": org.get("industry", "tech") if org else "tech",
                "org_size": org.get("size", "mid_market") if org else "mid_market",
            }

            if assessment.get("status") == "completed":
                return _toast_only("Already Complete", "This assessment is already completed. View it in Results.")

            dims = _get_ordered_dimensions(a_config["uses_databricks"])
            resume_dim = 0
            for i, dim in enumerate(dims):
                dim_questions = get_adaptive_questions(dim["id"], {}, a_config["uses_databricks"])
                has_answer = any(q["id"] in a_responses for q in dim_questions)
                if not has_answer:
                    resume_dim = i
                    break
                resume_dim = i

            return _render_dimension_full(
                dims, resume_dim, a_responses,
                assessment["id"], assessment["org_id"],
                a_config,
            )

        # ── Save button ──
        if triggered == "compass-save-btn":
            if assessment_id and responses:
                _persist_responses(assessment_id, responses)
                return _toast_only("Saved", f"Progress saved ({len(responses)} answers). You can resume later.")
            return _toast_only("Nothing to Save", "No assessment in progress.")

        # ── Back button ──
        if triggered == "compass-back-btn":
            if step == "questions" and current_dim > 0:
                # Persist before navigating back
                _persist_responses(assessment_id, responses)
                dims = _get_ordered_dimensions(cfg_databricks)
                current_dim -= 1
                return _render_dimension_full(
                    dims, current_dim, responses,
                    assessment_id, org_id, config,
                )
            elif step == "questions" and current_dim == 0:
                # Persist before returning to setup
                _persist_responses(assessment_id, responses)
                from ui.pages.compass_assessment import _create_setup_form, _build_resume_options
                resume_options = _build_resume_options()
                return (
                    _create_setup_form(resume_options),
                    _progress_style(0),
                    "",
                    [],
                    {"display": "none"},
                    {"display": "none"},
                    ["Next ", html.I(className="fas fa-arrow-right")],
                    "setup",
                    assessment_id, org_id, 0, responses, config,
                    False, "", "",
                    no_update,  # selected-assessment-id
                )
            return _no_update()

        # ── Next button ──
        if triggered == "compass-next-btn":
            # Setup step: validate form and create assessment
            if step == "setup":
                if not team_name or not team_name.strip():
                    return _toast_only("Validation Error", "Please enter a team name.")
                if not respondent_name or not respondent_name.strip():
                    return _toast_only("Validation Error", "Please enter your name.")
                if not respondent_role or not respondent_role.strip():
                    return _toast_only("Validation Error", "Please enter your role.")

                admin_cfg = get_admin_config()
                uses_databricks = admin_cfg.get("uses_databricks", False)
                weight_profile = admin_cfg.get("scoring_profile", "balanced")
                industry = admin_cfg.get("industry", "tech")
                org_size = admin_cfg.get("org_size", "mid_market")

                org = create_organization(
                    name=team_name.strip(),
                    industry=industry,
                    size=org_size,
                    cloud_provider="azure",
                    uses_databricks=bool(uses_databricks),
                )
                assessment = create_assessment(
                    org_id=org["id"],
                    assessment_type="full",
                    weight_profile=weight_profile,
                    respondent_name=respondent_name.strip(),
                    respondent_role=respondent_role.strip(),
                )
                if save_name and save_name.strip():
                    update_assessment(assessment["id"], {"save_name": save_name.strip()})

                new_config = {
                    "uses_databricks": bool(uses_databricks),
                    "weight_profile": weight_profile,
                    "industry": industry,
                    "org_size": org_size,
                }

                dims = _get_ordered_dimensions(new_config["uses_databricks"])
                return _render_dimension_full(
                    dims, 0, {},
                    assessment["id"], org["id"],
                    new_config,
                )

            # Questions step: persist and advance to next dimension
            if step == "questions":
                _persist_responses(assessment_id, responses)

                dims = _get_ordered_dimensions(cfg_databricks)
                if current_dim < len(dims) - 1:
                    current_dim += 1
                    return _render_dimension_full(
                        dims, current_dim, responses,
                        assessment_id, org_id, config,
                    )
                else:
                    return _submit_assessment(
                        assessment_id, org_id, responses, config,
                    )

        return _no_update()

    # ── CB3: Auto-save every 30 seconds ──
    @app.callback(
        Output("compass-autosave-status", "children"),
        Input("compass-autosave-interval", "n_intervals"),
        State("compass-wizard-step", "data"),
        State("compass-assessment-id", "data"),
        State("compass-responses", "data"),
        State("compass-live-answers", "data"),
        prevent_initial_call=True,
    )
    def autosave_responses(n_intervals, step, assessment_id, responses, live_answers):
        """Silently persist responses every 30 seconds while assessment is active."""
        if step != "questions" or not assessment_id:
            return no_update

        responses = responses or {}
        live_answers = live_answers or {}
        all_responses = {**responses, **live_answers}

        if not all_responses:
            return no_update

        _persist_responses(assessment_id, all_responses)
        return f"Auto-saved {len(all_responses)} answers at {datetime.now().strftime('%H:%M:%S')}"

    # ── CB4: Completion screen navigation buttons ──
    app.clientside_callback(
        """
        function(n1, n2) {
            if (!n1 && !n2) return window.dash_clientside.no_update;
            var ctx = window.dash_clientside.callback_context;
            if (!ctx.triggered || ctx.triggered.length === 0) return window.dash_clientside.no_update;
            var triggered = ctx.triggered[0].prop_id;
            if (triggered.indexOf('results') >= 0) return 'compass_results';
            if (triggered.indexOf('roadmap') >= 0) return 'compass_roadmap';
            return window.dash_clientside.no_update;
        }
        """,
        Output("current-page", "data", allow_duplicate=True),
        Input("compass-goto-results-btn", "n_clicks"),
        Input("compass-goto-roadmap-btn", "n_clicks"),
        prevent_initial_call=True,
    )


# ── Output count = 17 ──
_OUTPUT_COUNT = 17


def _no_update():
    return (no_update,) * _OUTPUT_COUNT


def _toast_only(header, message):
    return (
        no_update, no_update, no_update, no_update,
        no_update, no_update, no_update, no_update,
        no_update, no_update, no_update, no_update, no_update,
        True, header, message,
        no_update,  # selected-assessment-id
    )


def _progress_style(pct):
    return {
        "height": "4px", "backgroundColor": "#4B7BF5",
        "borderRadius": "2px", "transition": "width 0.3s ease",
        "width": f"{pct:.0f}%",
    }


def _persist_responses(assessment_id, responses):
    """Save all current responses to the assessment JSON store."""
    if not assessment_id or not responses:
        return
    for qid, resp in responses.items():
        if not isinstance(resp, dict):
            continue
        q = get_question(qid)
        dim = q.get("_dimension", "") if q else ""
        sub = q.get("_sub_dimension") if q else None
        save_response(
            assessment_id, qid, dim, sub,
            resp.get("response_type", "likert"),
            resp.get("response_value", {}),
        )


def _get_ordered_dimensions(uses_databricks: bool) -> list:
    load_all_dimensions()
    all_meta = get_dimension_metadata()
    dims = [m for m in all_meta if not m["is_databricks"]]
    if uses_databricks:
        dims.extend([m for m in all_meta if m["is_databricks"]])
    return dims


def _render_dimension_full(dims, current_dim, responses, assessment_id, org_id, config):
    if current_dim >= len(dims):
        current_dim = len(dims) - 1

    dim = dims[current_dim]
    dim_id = dim["id"]
    uses_db = config.get("uses_databricks", False)

    response_vals = {}
    for qid, r in responses.items():
        if isinstance(r, dict):
            rv = r.get("response_value", {})
            response_vals[qid] = rv

    questions = get_adaptive_questions(dim_id, response_vals, bool(uses_db))

    cards = []
    for q in questions:
        qid = q["id"]
        existing = None
        if qid in responses and isinstance(responses[qid], dict):
            existing = responses[qid].get("response_value")
        cards.append(create_question_card(q, existing))

    content = html.Div([
        html.Div([
            html.I(className=f"fas fa-{dim.get('icon', 'circle')}", style={
                "color": dim.get("color", "#4B7BF5"), "fontSize": "18px",
            }),
            html.Div([
                html.Div(dim["display_name"], style={
                    "color": "#E6EDF3", "fontSize": "16px", "fontWeight": "700",
                }),
                html.Div(dim.get("description", ""), style={
                    "color": "#8B949E", "fontSize": "12px",
                }),
            ]),
        ], style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "16px"}),
        html.Div(cards),
    ])

    total_dims = len(dims)
    progress_pct = ((current_dim + 1) / (total_dims + 1)) * 100
    progress_text = f"Dimension {current_dim + 1} of {total_dims}"

    tabs = []
    for i, d in enumerate(dims):
        is_current = i == current_dim
        is_done = i < current_dim
        tab_color = d.get("color", "#4B7BF5") if is_current else ("#34D399" if is_done else "#484F58")
        tabs.append(html.Div(
            d["display_name"][:12],
            style={
                "padding": "4px 10px",
                "borderRadius": "4px",
                "fontSize": "11px",
                "fontWeight": "600" if is_current else "400",
                "color": "#E6EDF3" if is_current else ("#8B949E" if is_done else "#484F58"),
                "backgroundColor": f"{tab_color}22" if is_current else "transparent",
                "borderBottom": f"2px solid {tab_color}" if is_current or is_done else "2px solid transparent",
                "whiteSpace": "nowrap",
            },
        ))

    is_last = current_dim >= len(dims) - 1
    next_label = (
        [html.I(className="fas fa-check"), " Submit Assessment"]
        if is_last
        else ["Next ", html.I(className="fas fa-arrow-right")]
    )

    return (
        content,
        _progress_style(progress_pct),
        progress_text,
        tabs,
        {"display": "inline-block"},
        {"display": "inline-block"},
        next_label,
        "questions",
        assessment_id,
        org_id,
        current_dim,
        responses,
        config,
        False, "", "",
        no_update,  # selected-assessment-id
    )


def _submit_assessment(assessment_id, org_id, responses, config):
    weight_profile = config.get("weight_profile", "balanced")
    uses_databricks = config.get("uses_databricks", False)
    industry = config.get("industry", "tech")
    org_size = config.get("org_size", "mid_market")

    # Persist all responses before scoring
    _persist_responses(assessment_id, responses)

    result = full_score_assessment(responses, weight_profile, uses_databricks)
    dim_scores = result["dimension_scores"]
    composite = result["composite"]
    indicators = result["indicators"]

    anti_patterns = detect_anti_patterns(indicators, include_databricks=uses_databricks)

    breakdown = composite.get("dimension_breakdown", {})
    roadmap = generate_roadmap(breakdown, "next_tier", anti_patterns)

    benchmark_comparison = compare_to_benchmarks(dim_scores, industry, org_size)

    save_scores(assessment_id, dim_scores, composite, anti_patterns, roadmap)
    update_assessment(assessment_id, {"benchmark_comparison": benchmark_comparison})

    overall = composite.get("overall_score", 0)
    overall_level = composite.get("overall_level", 1)
    overall_label = composite.get("overall_label", "Initial")
    overall_color = composite.get("overall_color", "#4B7BF5")

    content = html.Div([
        html.Div([
            html.I(className="fas fa-check-circle", style={
                "fontSize": "48px", "color": "#34D399", "marginBottom": "16px",
            }),
            html.Div("Assessment Complete!", style={
                "color": "#E6EDF3", "fontSize": "22px", "fontWeight": "700",
            }),
            html.Div([
                html.Span("Your overall maturity score: ", style={"color": "#8B949E"}),
                html.Span(f"{overall:.0f}/100", style={"color": overall_color, "fontWeight": "700", "fontSize": "20px"}),
                html.Span(f" -- L{overall_level} {overall_label}", style={"color": "#8B949E"}),
            ], style={"marginTop": "8px", "fontSize": "16px"}),
            html.Div([
                html.Span(f"{len(anti_patterns)} anti-patterns detected", style={
                    "color": "#FBBF24" if anti_patterns else "#34D399",
                }),
            ], style={"marginTop": "8px"}),

            # Direct navigation buttons
            html.Div([
                dbc.Button(
                    [html.I(className="fas fa-chart-bar"), " View Results"],
                    id="compass-goto-results-btn",
                    color="primary",
                    size="sm",
                    style={"marginRight": "12px"},
                ),
                dbc.Button(
                    [html.I(className="fas fa-road"), " View Roadmap"],
                    id="compass-goto-roadmap-btn",
                    color="info",
                    outline=True,
                    size="sm",
                ),
            ], style={"marginTop": "24px"}),
        ], style={"textAlign": "center", "padding": "60px 40px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "border": "1px solid var(--border, #272D3F)",
    })

    return (
        content,
        {"height": "4px", "backgroundColor": "#34D399", "borderRadius": "2px", "width": "100%"},
        "Complete!",
        [],
        {"display": "none"},
        {"display": "none"},
        ["Done"],
        "complete",
        assessment_id,
        org_id,
        0,
        responses,
        config,
        True, "Assessment Scored", f"Overall: {overall:.0f}/100 -- L{overall_level} {overall_label}",
        assessment_id,  # Set selected-assessment-id for cross-page sharing
    )
