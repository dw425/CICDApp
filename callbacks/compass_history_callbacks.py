"""Callbacks for Pipeline Compass History Page."""

from dash import Input, Output

from compass.assessment_store import (
    get_completed_assessments,
    get_all_organizations,
    get_organization,
)


def register_callbacks(app):
    """Register compass history callbacks."""

    @app.callback(
        Output("compass-history-content", "children"),
        Input("current-page", "data"),
    )
    def render_history(current_page):
        """Render history dashboard when page loads."""
        if current_page != "compass_history":
            from dash import no_update
            return no_update

        assessments = get_completed_assessments()
        orgs = {}
        for a in assessments:
            oid = a.get("org_id", "")
            if oid not in orgs:
                org = get_organization(oid)
                if org:
                    orgs[oid] = org

        from ui.pages.compass_history import create_history_dashboard
        return create_history_dashboard(assessments, orgs)
