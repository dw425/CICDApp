"""
Callbacks for Pipeline Compass Roadmap Page.

Handles: assessment selector population and roadmap rendering.
Only fires when user is on the compass_roadmap page.
"""

from dash import html, Input, Output, State, ctx, no_update

from compass.assessment_store import (
    get_assessment,
    get_organization,
    get_completed_assessments,
)
from compass.roadmap_engine import generate_roadmap


def register_callbacks(app):
    """Register all compass roadmap callbacks."""

    # ── CB1: Load selector when page renders ──
    @app.callback(
        Output("compass-roadmap-selector", "options"),
        Output("compass-roadmap-selector", "value"),
        Input("current-page", "data"),
        State("compass-roadmap-selector", "value"),
        State("selected-assessment-id", "data"),
        prevent_initial_call=True,
    )
    def load_roadmap_selector(current_page, existing_value, shared_assessment_id):
        """Populate the assessment selector when navigating to roadmap page."""
        if current_page != "compass_roadmap":
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

        # Prefer shared assessment ID, then existing, then first
        value = None
        valid_ids = {o["value"] for o in options}
        if shared_assessment_id and shared_assessment_id in valid_ids:
            value = shared_assessment_id
        elif existing_value and existing_value in valid_ids:
            value = existing_value
        elif options:
            value = options[0]["value"]

        return options, value

    # ── CB2: Render roadmap when selector or target changes ──
    @app.callback(
        Output("compass-roadmap-content", "children"),
        Input("compass-roadmap-selector", "value"),
        Input("compass-roadmap-target", "value"),
        prevent_initial_call=True,
    )
    def render_roadmap(assessment_id, target_profile):
        """Render the roadmap dashboard for the selected assessment."""
        if not assessment_id:
            from ui.pages.compass_roadmap import _create_empty_state
            return _create_empty_state()

        assessment = get_assessment(assessment_id)
        if not assessment or assessment.get("status") != "completed":
            from ui.pages.compass_roadmap import _create_empty_state
            return _create_empty_state()

        composite = assessment.get("composite", {})
        dim_scores = assessment.get("scores", {})
        anti_patterns = assessment.get("anti_patterns", [])

        breakdown = composite.get("dimension_breakdown", {})
        target = target_profile or "next_tier"

        roadmap = generate_roadmap(
            dimension_scores=breakdown,
            target_profile=target,
            anti_patterns=anti_patterns,
        )

        from ui.pages.compass_roadmap import create_roadmap_dashboard
        return create_roadmap_dashboard(roadmap, dim_scores)
