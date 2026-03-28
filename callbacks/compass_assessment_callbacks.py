"""Callbacks for Pipeline Compass Assessment — Single Page.
CB0: Reset stores on page entry.
CB1: Clientside response capture (browser-side, no round-trip).
CB2: Submit — validate, create org/assessment, score, save results.
CB3: Save — persist progress without scoring.
CB4: Autosave every 30s.
CB5: Resume — reload a saved assessment.
CB6: Completion nav (goto results/roadmap).
"""

from datetime import datetime
from dash import html, Input, Output, State, ctx, no_update, ALL
import dash_bootstrap_components as dbc

from compass.question_bank.loader import (
    load_all_dimensions,
    get_question,
)
from compass.assessment_store import (
    create_organization,
    create_assessment,
    get_assessment,
    get_organization,
    save_response,
    save_scores,
    update_assessment,
)
from compass.scoring_engine import full_score_assessment
from compass.antipattern_engine import detect_anti_patterns
from compass.roadmap_engine import generate_roadmap
from compass.benchmark_data import compare_to_benchmarks
from compass.admin_config import get_admin_config


def register_callbacks(app):
    """Register all compass assessment callbacks."""

    # ── CB0: Reset stores on page entry ──
    @app.callback(
        Output("compass-assessment-id", "data", allow_duplicate=True),
        Output("compass-org-id", "data", allow_duplicate=True),
        Output("compass-responses", "data", allow_duplicate=True),
        Output("compass-live-answers", "data", allow_duplicate=True),
        Output("compass-config", "data", allow_duplicate=True),
        Output("compass-wizard-step", "data", allow_duplicate=True),
        Output("compass-current-dim", "data", allow_duplicate=True),
        Input("current-page", "data"),
        prevent_initial_call=True,
    )
    def reset_on_page_entry(current_page):
        if current_page == "compass_assessment":
            return None, None, {}, {}, {}, "ready", 0
        return (no_update,) * 7

    # ── CB1: Clientside response capture ──
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

    # ── CB2: Submit Assessment ──
    @app.callback(
        Output("compass-status-area", "children"),
        Output("compass-toast", "is_open", allow_duplicate=True),
        Output("compass-toast", "header", allow_duplicate=True),
        Output("compass-toast", "children", allow_duplicate=True),
        Output("compass-assessment-id", "data", allow_duplicate=True),
        Output("compass-org-id", "data", allow_duplicate=True),
        Output("compass-responses", "data", allow_duplicate=True),
        Output("compass-config", "data", allow_duplicate=True),
        Output("selected-assessment-id", "data", allow_duplicate=True),
        Input("compass-submit-btn", "n_clicks"),
        State("compass-live-answers", "data"),
        State("compass-responses", "data"),
        State("compass-assessment-id", "data"),
        State("compass-org-id", "data"),
        State("compass-config", "data"),
        State("compass-org-name", "value"),
        State("compass-respondent-name", "value"),
        State("compass-respondent-role", "value"),
        State("compass-save-name", "value"),
        prevent_initial_call=True,
    )
    def submit_assessment(
        n_clicks,
        live_answers, stored_responses, assessment_id, org_id, config,
        team_name, respondent_name, respondent_role, save_name,
    ):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        # Merge responses
        responses = {**(stored_responses or {}), **(live_answers or {})}

        if not responses:
            return (
                no_update,
                True, "No Answers", "Please answer at least some questions before submitting.",
                no_update, no_update, no_update, no_update, no_update,
            )

        # Validate team info
        if not team_name or not team_name.strip():
            return (
                no_update,
                True, "Missing Info", "Please enter a team name at the top of the page.",
                no_update, no_update, no_update, no_update, no_update,
            )
        if not respondent_name or not respondent_name.strip():
            return (
                no_update,
                True, "Missing Info", "Please enter your name at the top of the page.",
                no_update, no_update, no_update, no_update, no_update,
            )
        if not respondent_role or not respondent_role.strip():
            return (
                no_update,
                True, "Missing Info", "Please enter your role at the top of the page.",
                no_update, no_update, no_update, no_update, no_update,
            )

        # Create org + assessment if not already created
        admin_cfg = get_admin_config()
        uses_databricks = admin_cfg.get("uses_databricks", False)
        weight_profile = admin_cfg.get("scoring_profile", "balanced")
        industry = admin_cfg.get("industry", "tech")
        org_size = admin_cfg.get("org_size", "mid_market")

        if not assessment_id:
            org = create_organization(
                name=team_name.strip(),
                industry=industry,
                size=org_size,
                cloud_provider="azure",
                uses_databricks=bool(uses_databricks),
            )
            org_id = org["id"]
            assessment = create_assessment(
                org_id=org_id,
                assessment_type="full",
                weight_profile=weight_profile,
                respondent_name=respondent_name.strip(),
                respondent_role=respondent_role.strip(),
            )
            assessment_id = assessment["id"]
            if save_name and save_name.strip():
                update_assessment(assessment_id, {"save_name": save_name.strip()})

        new_config = {
            "uses_databricks": bool(uses_databricks),
            "weight_profile": weight_profile,
            "industry": industry,
            "org_size": org_size,
        }

        # Persist all responses
        _persist_responses(assessment_id, responses)

        # Score
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

        # Build completion banner
        status_content = html.Div([
            html.Div([
                html.I(className="fas fa-check-circle", style={
                    "fontSize": "42px", "color": "#34D399", "marginBottom": "12px",
                }),
                html.Div("Assessment Complete!", style={
                    "color": "#E6EDF3", "fontSize": "22px", "fontWeight": "700",
                }),
                html.Div([
                    html.Span("Overall maturity score: ", style={"color": "#8B949E"}),
                    html.Span(f"{overall:.0f}/100", style={
                        "color": overall_color, "fontWeight": "700", "fontSize": "20px",
                    }),
                    html.Span(f"  —  L{overall_level} {overall_label}", style={"color": "#8B949E"}),
                ], style={"marginTop": "8px", "fontSize": "16px"}),
                html.Div([
                    html.Span(f"{len(anti_patterns)} anti-patterns detected", style={
                        "color": "#FBBF24" if anti_patterns else "#34D399",
                    }),
                ], style={"marginTop": "6px"}),
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
                ], style={"marginTop": "20px"}),
            ], style={"textAlign": "center", "padding": "40px 24px"}),
        ], style={
            "backgroundColor": "var(--surface, #161B22)",
            "borderRadius": "8px",
            "border": "1px solid #34D399",
            "marginTop": "16px",
            "marginBottom": "16px",
        })

        return (
            status_content,
            True, "Assessment Scored",
            f"Overall: {overall:.0f}/100 — L{overall_level} {overall_label}",
            assessment_id, org_id, responses, new_config,
            assessment_id,
        )

    # ── CB3: Save Progress ──
    @app.callback(
        Output("compass-toast", "is_open", allow_duplicate=True),
        Output("compass-toast", "header", allow_duplicate=True),
        Output("compass-toast", "children", allow_duplicate=True),
        Output("compass-assessment-id", "data", allow_duplicate=True),
        Output("compass-org-id", "data", allow_duplicate=True),
        Output("compass-responses", "data", allow_duplicate=True),
        Output("compass-config", "data", allow_duplicate=True),
        Input("compass-save-btn", "n_clicks"),
        State("compass-live-answers", "data"),
        State("compass-responses", "data"),
        State("compass-assessment-id", "data"),
        State("compass-org-id", "data"),
        State("compass-config", "data"),
        State("compass-org-name", "value"),
        State("compass-respondent-name", "value"),
        State("compass-respondent-role", "value"),
        State("compass-save-name", "value"),
        prevent_initial_call=True,
    )
    def save_progress(
        n_clicks,
        live_answers, stored_responses, assessment_id, org_id, config,
        team_name, respondent_name, respondent_role, save_name,
    ):
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update

        responses = {**(stored_responses or {}), **(live_answers or {})}

        if not responses:
            return True, "Nothing to Save", "Answer some questions first.", no_update, no_update, no_update, no_update

        if not team_name or not team_name.strip():
            return True, "Missing Info", "Please enter a team name.", no_update, no_update, no_update, no_update

        # Create org + assessment if needed
        admin_cfg = get_admin_config()
        uses_databricks = admin_cfg.get("uses_databricks", False)
        weight_profile = admin_cfg.get("scoring_profile", "balanced")
        industry = admin_cfg.get("industry", "tech")
        org_size = admin_cfg.get("org_size", "mid_market")

        if not assessment_id:
            org = create_organization(
                name=team_name.strip(),
                industry=industry,
                size=org_size,
                cloud_provider="azure",
                uses_databricks=bool(uses_databricks),
            )
            org_id = org["id"]
            assessment = create_assessment(
                org_id=org_id,
                assessment_type="full",
                weight_profile=weight_profile,
                respondent_name=(respondent_name or "").strip() or "Unknown",
                respondent_role=(respondent_role or "").strip() or "Unknown",
            )
            assessment_id = assessment["id"]
            if save_name and save_name.strip():
                update_assessment(assessment_id, {"save_name": save_name.strip()})

        new_config = {
            "uses_databricks": bool(uses_databricks),
            "weight_profile": weight_profile,
            "industry": industry,
            "org_size": org_size,
        }

        _persist_responses(assessment_id, responses)

        return (
            True, "Saved",
            f"Progress saved — {len(responses)} answers. You can resume this later.",
            assessment_id, org_id, responses, new_config,
        )

    # ── CB4: Autosave every 30s ──
    @app.callback(
        Output("compass-autosave-status", "children"),
        Input("compass-autosave-interval", "n_intervals"),
        State("compass-assessment-id", "data"),
        State("compass-responses", "data"),
        State("compass-live-answers", "data"),
        prevent_initial_call=True,
    )
    def autosave(n_intervals, assessment_id, responses, live_answers):
        if not assessment_id:
            return no_update
        all_resp = {**(responses or {}), **(live_answers or {})}
        if not all_resp:
            return no_update
        _persist_responses(assessment_id, all_resp)
        return f"Auto-saved {len(all_resp)} answers at {datetime.now().strftime('%H:%M:%S')}"

    # ── CB5: Resume saved assessment (toast only — page reloads with all questions) ──
    @app.callback(
        Output("compass-toast", "is_open", allow_duplicate=True),
        Output("compass-toast", "header", allow_duplicate=True),
        Output("compass-toast", "children", allow_duplicate=True),
        Output("compass-assessment-id", "data", allow_duplicate=True),
        Output("compass-org-id", "data", allow_duplicate=True),
        Output("compass-responses", "data", allow_duplicate=True),
        Output("compass-config", "data", allow_duplicate=True),
        Output("compass-live-answers", "data", allow_duplicate=True),
        Input("compass-resume-btn", "n_clicks"),
        State("compass-resume-selector", "value"),
        prevent_initial_call=True,
    )
    def resume_assessment(n_clicks, resume_id):
        if not n_clicks or not resume_id:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        assessment = get_assessment(resume_id)
        if not assessment:
            return True, "Error", "Assessment not found.", no_update, no_update, no_update, no_update, no_update

        if assessment.get("status") == "completed":
            return True, "Already Complete", "This assessment is completed. View it in Results.", no_update, no_update, no_update, no_update, no_update

        # Rebuild responses
        a_responses = {}
        raw = assessment.get("responses", {})
        for qid, r in raw.items():
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

        return (
            True, "Resumed",
            f"Loaded {len(a_responses)} saved answers. They are stored — fill in remaining questions and submit.",
            assessment["id"], assessment.get("org_id"), a_responses, a_config,
            a_responses,
        )

    # ── CB6: Completion nav buttons ──
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


def _persist_responses(assessment_id, responses):
    """Save all responses to the assessment store."""
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
