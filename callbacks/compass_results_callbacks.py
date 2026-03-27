"""
Callbacks for Pipeline Compass Results Dashboard.
# ****Truth Agent Verified**** — CB1: load selector with shared-assessment-id. CB2: render results.
# CB3: PDF/PPTX export. CB4: CSV export. CB5: JSON export. BUG5: shared selector integration.

Handles: assessment selector population, results rendering, PDF/PPTX export.
Only fires when the user is on the compass_results page.
"""

from dash import html, Input, Output, State, ctx, no_update, dcc, callback_context

from compass.assessment_store import (
    get_assessment,
    get_organization,
    get_completed_assessments,
)
from compass.benchmark_data import compare_to_benchmarks


def register_callbacks(app):
    """Register all compass results callbacks."""

    # ── CB1: Load selector options when page renders ──
    @app.callback(
        Output("compass-results-selector", "options"),
        Output("compass-results-selector", "value"),
        Input("current-page", "data"),
        State("compass-results-selector", "value"),
        State("selected-assessment-id", "data"),
        prevent_initial_call=True,
    )
    def load_results_selector(current_page, existing_value, shared_assessment_id):
        """Populate the assessment selector dropdown when navigating to results page."""
        if current_page != "compass_results":
            return no_update, no_update

        assessments = get_completed_assessments()
        options = []
        for a in assessments:
            org = get_organization(a.get("org_id", ""))
            org_name = org["name"] if org else "Unknown"
            composite = a.get("composite", {})
            score = composite.get("overall_score", 0)
            label = composite.get("overall_label", "")
            date = (a.get("completed_at") or a.get("created_at", ""))[:10]
            options.append({
                "label": f"{org_name} — {score:.0f}/100 ({label}) — {date}",
                "value": a["id"],
            })

        # Prefer shared assessment ID (from just-completed assessment), then existing, then first
        value = None
        valid_ids = {o["value"] for o in options}
        if shared_assessment_id and shared_assessment_id in valid_ids:
            value = shared_assessment_id
        elif existing_value and existing_value in valid_ids:
            value = existing_value
        elif options:
            value = options[0]["value"]

        return options, value

    # ── CB2: Render results dashboard when selector changes ──
    @app.callback(
        Output("compass-results-content", "children"),
        Output("compass-results-subtitle", "children"),
        Input("compass-results-selector", "value"),
        prevent_initial_call=True,
    )
    def render_results(assessment_id):
        """Render the results dashboard for the selected assessment."""
        if not assessment_id:
            from ui.pages.compass_results import _create_empty_state
            return _create_empty_state(), "Select an assessment to view results"

        assessment = get_assessment(assessment_id)
        if not assessment or assessment.get("status") != "completed":
            from ui.pages.compass_results import _create_empty_state
            return _create_empty_state(), "Assessment not found or not completed"

        org = get_organization(assessment.get("org_id", ""))
        if not org:
            org = {"name": "Unknown", "industry": "all", "size": "mid_market"}

        composite = assessment.get("composite", {})
        dim_scores = assessment.get("scores", {})
        anti_patterns = assessment.get("anti_patterns", [])
        roadmap = assessment.get("roadmap", {})
        benchmark_comparison = assessment.get("benchmark_comparison")

        if not benchmark_comparison:
            benchmark_comparison = compare_to_benchmarks(
                dim_scores,
                org.get("industry", "all"),
                org.get("size", "mid_market"),
            )

        from ui.pages.compass_results import create_results_dashboard
        dashboard = create_results_dashboard(
            assessment=assessment,
            org=org,
            composite=composite,
            dimension_scores=dim_scores,
            anti_patterns=anti_patterns,
            roadmap=roadmap,
            benchmark_comparison=benchmark_comparison,
        )

        subtitle = f"{org['name']} — {composite.get('overall_label', '')} (L{composite.get('overall_level', 1)})"
        return dashboard, subtitle

    # ── CB3: Handle PDF/PPTX export ──
    @app.callback(
        Output("compass-download", "data"),
        Output("compass-results-toast", "is_open"),
        Output("compass-results-toast", "header"),
        Output("compass-results-toast", "children"),
        Input("compass-export-pdf-btn", "n_clicks"),
        Input("compass-export-pptx-btn", "n_clicks"),
        State("compass-results-selector", "value"),
        prevent_initial_call=True,
    )
    def handle_export(pdf_clicks, pptx_clicks, assessment_id):
        """Handle PDF and PPTX export button clicks."""
        triggered = ctx.triggered_id
        if not triggered or not assessment_id:
            return no_update, False, "", ""

        assessment = get_assessment(assessment_id)
        if not assessment:
            return no_update, True, "Error", "Assessment not found"

        org = get_organization(assessment.get("org_id", ""))
        if not org:
            org = {"name": "Unknown"}
        org_name = org.get("name", "Unknown")

        if triggered == "compass-export-pdf-btn":
            try:
                from compass.export_pdf import generate_pdf_report
                pdf_bytes = generate_pdf_report(assessment, org)
                return (
                    dcc.send_bytes(pdf_bytes, f"compass_report_{org_name.replace(' ', '_')}.pdf"),
                    True, "Export Complete", "PDF report downloaded successfully.",
                )
            except Exception as e:
                return no_update, True, "Export Error", f"PDF generation failed: {str(e)}"

        elif triggered == "compass-export-pptx-btn":
            try:
                from compass.export_pptx import generate_pptx_report
                pptx_bytes = generate_pptx_report(assessment, org)
                return (
                    dcc.send_bytes(pptx_bytes, f"compass_deck_{org_name.replace(' ', '_')}.pptx"),
                    True, "Export Complete", "PPTX deck downloaded successfully.",
                )
            except Exception as e:
                return no_update, True, "Export Error", f"PPTX generation failed: {str(e)}"

        return no_update, False, "", ""

    # ── CB4: CSV export ──
    @app.callback(
        Output("compass-download-csv", "data"),
        Input("compass-export-csv-btn", "n_clicks"),
        State("compass-results-selector", "value"),
        prevent_initial_call=True,
    )
    def export_csv(n_clicks, assessment_id):
        """Export assessment data as CSV."""
        if not n_clicks or not assessment_id:
            return no_update

        assessment = get_assessment(assessment_id)
        if not assessment:
            return no_update

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Dimension", "Score", "Level", "Label", "Weight"])

        composite = assessment.get("composite", {})
        breakdown = composite.get("dimension_breakdown", {})
        for dim_id, data in breakdown.items():
            writer.writerow([
                dim_id,
                data.get("score", ""),
                data.get("level", ""),
                data.get("label", ""),
                data.get("weight", ""),
            ])

        org = get_organization(assessment.get("org_id", ""))
        org_name = org.get("name", "export") if org else "export"
        return dict(
            content=output.getvalue(),
            filename=f"compass_scores_{org_name.replace(' ', '_')}.csv",
        )

    # ── CB5: JSON export ──
    @app.callback(
        Output("compass-download-json", "data"),
        Input("compass-export-json-btn", "n_clicks"),
        State("compass-results-selector", "value"),
        prevent_initial_call=True,
    )
    def export_json(n_clicks, assessment_id):
        """Export full assessment record as JSON."""
        if not n_clicks or not assessment_id:
            return no_update

        import json as json_mod

        assessment = get_assessment(assessment_id)
        if not assessment:
            return no_update

        export_data = {k: v for k, v in assessment.items() if not k.startswith("_")}

        org = get_organization(assessment.get("org_id", ""))
        org_name = org.get("name", "export") if org else "export"
        return dict(
            content=json_mod.dumps(export_data, indent=2, default=str),
            filename=f"compass_assessment_{org_name.replace(' ', '_')}.json",
        )
